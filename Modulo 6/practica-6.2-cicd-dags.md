# Práctica 6.2: CI/CD para DAGs de Airflow

**Duración estimada:** 30-45 minutos  
**Requisitos previos:** Práctica 6.1 completada. Airflow, Jenkins, y GitLab configurados.

---

## Objetivo

Implementar pipeline CI/CD que:
1. Valida DAGs nuevos (estructura, imports).
2. Ejecuta tests automáticos.
3. Copia DAGs a carpeta de Airflow si todo pasa.
4. Airflow rescaneaautomáticamente.

---

## Conceptos Base (5 min)

### El Problema: Deployar DAGs Manualmente

Sin CI/CD:

```
1. Data Engineer escribe DAG en local
2. Testea en Airflow local
3. Manualmente copia archivo a servidor Airflow
4. Espera a que scheduler reescaneae (puede tardar minutos)
5. ¿Si hay error? Buscar logs manualmente
```

Frágil y lento.

### Con CI/CD:

```
1. Data Engineer hace push a Git
2. Pipeline detecta cambios en dags/
3. Tests corren automáticamente
4. Si OK, copiar a servidor Airflow
5. Scheduler rescaneaautomáticamente
6. ¡DAG vivo en 1 minuto!
```

---

## Fase 1: Crear Tests para DAGs (10 min)

### Paso 1.1: Crear estructura de tests

```bash
cd ~/formacion-cd/airflow
mkdir -p tests
touch tests/__init__.py tests/test_etl_usuarios_dag.py
```

### Paso 1.2: Test de estructura del DAG

**tests/test_etl_usuarios_dag.py:**

```python
#!/usr/bin/env python3
"""
Tests para validar DAG etl_usuarios.
"""
import sys
import os
import pytest
from datetime import datetime

# Agregar dags al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dags'))

from etl_usuarios_dag import dag


class TestETLUsuariosDAG:
    """Tests de DAG."""
    
    def test_dag_exists(self):
        """Validar que DAG existe."""
        assert dag is not None
    
    def test_dag_id(self):
        """Validar ID del DAG."""
        assert dag.dag_id == 'etl_usuarios'
    
    def test_dag_has_tasks(self):
        """Validar que DAG tiene tasks."""
        assert len(dag.tasks) == 4, f"Expected 4 tasks, got {len(dag.tasks)}"
    
    def test_task_ids(self):
        """Validar que tasks tienen IDs esperados."""
        task_ids = [task.task_id for task in dag.tasks]
        expected_ids = ['extract_usuarios', 'transform_usuarios', 'load_usuarios', 'validate_load']
        
        for expected_id in expected_ids:
            assert expected_id in task_ids, f"Task {expected_id} not found"
    
    def test_dag_has_dependencies(self):
        """Validar que tasks tienen dependencias."""
        # extract_usuarios debe ser raíz
        extract_task = dag.tasks_dict['extract_usuarios']
        assert len(extract_task.upstream_list) == 0, "extract debe ser tarea inicial"
        
        # transform debe depender de extract
        transform_task = dag.tasks_dict['transform_usuarios']
        assert extract_task in transform_task.upstream_list, "transform debe depender de extract"
        
        # validate debe ser última
        validate_task = dag.tasks_dict['validate_load']
        assert len([t for t in dag.tasks if t in validate_task.upstream_list]) > 0, "validate debe tener dependencias"
    
    def test_dag_scheduling(self):
        """Validar que DAG tiene schedule."""
        assert dag.schedule_interval is not None, "DAG debe tener schedule_interval"
    
    def test_dag_start_date(self):
        """Validar que DAG tiene start_date."""
        assert dag.start_date is not None, "DAG debe tener start_date"
    
    def test_no_cycles(self):
        """Validar que no hay ciclos en DAG (acíclico)."""
        # Airflow valida esto automáticamente, pero podemos validar
        try:
            # Llamar a método que detecta ciclos
            dag.validate_dagrun()
            assert True, "DAG no tiene ciclos"
        except Exception as e:
            pytest.fail(f"DAG tiene ciclos o error: {str(e)}")
```

### Paso 1.3: Test de validación de syntax

**tests/test_dags_syntax.py:**

```python
#!/usr/bin/env python3
"""
Tests de syntax para todos los DAGs.
"""
import os
import sys
import py_compile
import pytest

# Directorio de DAGs
DAGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'dags')


class TestDAGsSyntax:
    """Validar que todos los DAGs tienen syntax correcto."""
    
    def test_all_dag_files_compile(self):
        """Validar que archivos Python compilan correctamente."""
        for filename in os.listdir(DAGS_DIR):
            if filename.endswith('_dag.py'):
                filepath = os.path.join(DAGS_DIR, filename)
                try:
                    py_compile.compile(filepath, doraise=True)
                    print(f"✓ {filename} compila correctamente")
                except py_compile.PyCompileError as e:
                    pytest.fail(f"Syntax error en {filename}: {str(e)}")
    
    def test_all_dag_files_import(self):
        """Validar que DAGs pueden importarse."""
        sys.path.insert(0, DAGS_DIR)
        
        for filename in os.listdir(DAGS_DIR):
            if filename.endswith('_dag.py'):
                module_name = filename[:-3]  # Quitar .py
                try:
                    __import__(module_name)
                    print(f"✓ {module_name} importa correctamente")
                except ImportError as e:
                    pytest.fail(f"Import error en {module_name}: {str(e)}")
```

### Paso 1.4: Instalar pytest localmente

```bash
pip install pytest apache-airflow pandas psycopg2-binary --user
```

### Paso 1.5: Ejecutar tests localmente

```bash
cd ~/formacion-cd/airflow
pytest tests/ -v
```

Deberías ver:

```
tests/test_etl_usuarios_dag.py::TestETLUsuariosDAG::test_dag_exists PASSED
tests/test_etl_usuarios_dag.py::TestETLUsuariosDAG::test_dag_id PASSED
tests/test_etl_usuarios_dag.py::TestETLUsuariosDAG::test_dag_has_tasks PASSED
...
tests/test_dags_syntax.py::TestDAGsSyntax::test_all_dag_files_compile PASSED
tests/test_dags_syntax.py::TestDAGsSyntax::test_all_dag_files_import PASSED

====== 10 passed ======
```

### ✓ Checkpoint 1: Tests locales pasando

---

## Fase 2: Pipeline CI/CD en Jenkins (15 min)

### Paso 2.1: Crear Jenkinsfile para Airflow

En el directorio raíz de airflow, crear **Jenkinsfile:**

```groovy
pipeline {
    agent any
    
    environment {
        AIRFLOW_HOME = '/opt/airflow'
        DAGS_FOLDER = '${AIRFLOW_HOME}/dags'
    }
    
    stages {
        stage('Validate DAGs Syntax') {
            steps {
                echo "=== Validando syntax de archivos DAG ==="
                sh '''
                    find dags/ -name "*_dag.py" -exec python3 -m py_compile {} \\;
                    echo "✓ Todos los DAGs compilan"
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                echo "=== Ejecutando tests ==="
                sh '''
                    pip install pytest apache-airflow pandas psycopg2-binary
                    pytest tests/ -v --tb=short
                    echo "✓ Tests pasaron"
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo "=== Build stage ==="
                sh '''
                    echo "No build necesario para DAGs"
                    echo "✓ Build OK"
                '''
            }
        }
        
        stage('Deploy DAGs') {
            when {
                branch 'main'  // Solo en merge a main
            }
            steps {
                echo "=== Deployando DAGs ==="
                sh '''
                    # Copiar DAGs a carpeta de Airflow
                    # En caso real, usaría SCP/SSH a servidor
                    echo "Copiaría DAGs a servidor Airflow aquí"
                    echo "scp -r dags/* airflow@prod-server:/opt/airflow/dags/"
                    echo "✓ DAGs desplegados"
                '''
            }
        }
        
        stage('Trigger Scheduler Rescan') {
            when {
                branch 'main'
            }
            steps {
                echo "=== Pidiendo rescaneade DAGs ==="
                sh '''
                    # En caso real, llamaría a API de Airflow
                    echo "curl -X POST http://airflow-server:8080/api/v1/dags/refresh"
                    echo "✓ Scheduler rescaneará en próximos 30 segundos"
                '''
            }
        }
    }
    
    post {
        always {
            echo "=== Pipeline completada ==="
        }
        success {
            echo "✓ Pipeline exitosa - DAGs deployados"
        }
        failure {
            echo "✗ Pipeline falló - No se desplegaron DAGs"
        }
    }
}
```

### Paso 2.2: Crear repo Git y commit

```bash
cd ~/formacion-cd/airflow
git init
git add Jenkinsfile dags/ tests/ .gitignore
git commit -m "Initial Airflow repo with CI/CD"
```

### Paso 2.3: Crear Pipeline Job en Jenkins

1. Jenkins: "New Item"
2. Name: `airflow-dags-cicd`
3. Type: **Pipeline**
4. En "Definition": **Pipeline script**
5. Pegar Jenkinsfile
6. En "General", agregar trigger: **Poll SCM** con `H/5 * * * *` (cada 5 minutos)
7. Click "Save"

### Paso 2.4: Ejecutar Pipeline

1. "Build Now"
2. Ver Console Output

Deberías ver:

```
=== Validando syntax ===
✓ Todos los DAGs compilan

=== Ejecutando tests ===
pytest tests/...
10 passed

=== Deploy DAGs ===
✓ DAGs desplegados
```

### ✓ Checkpoint 2: Pipeline Jenkins exitosa

---

## Fase 3: Pipeline CI/CD en GitLab (15 min)

### Paso 3.1: Crear repo en GitLab

1. GitLab: "New project"
2. Name: `airflow-dags`
3. Visibility: Public
4. Click "Create"

### Paso 3.2: Clone y push

```bash
cd ~/formacion-cd
git clone http://localhost:81/root/airflow-dags.git
cd airflow-dags

# Copiar archivos de Airflow
cp -r ~/formacion-cd/airflow/dags .
cp -r ~/formacion-cd/airflow/tests .
mkdir -p data
touch .gitignore
```

### Paso 3.3: Crear .gitlab-ci.yml

```yaml
stages:
  - validate
  - test
  - deploy

variables:
  AIRFLOW_HOME: /opt/airflow
  DAGS_FOLDER: /opt/airflow/dags

validate_syntax:
  stage: validate
  image: python:3.11
  script:
    - echo "=== Validando syntax de DAGs ==="
    - find dags/ -name "*_dag.py" -exec python3 -m py_compile {} \;
    - echo "✓ Todos los DAGs compilan"

test_dags:
  stage: test
  image: python:3.11
  script:
    - echo "=== Ejecutando tests ==="
    - pip install pytest apache-airflow pandas psycopg2-binary -q
    - pytest tests/ -v --tb=short
    - echo "✓ Tests pasaron"
  artifacts:
    reports:
      junit: test-results.xml
    expire_in: 1 week

deploy_dags:
  stage: deploy
  image: alpine:latest
  script:
    - echo "=== Deployando DAGs ==="
    - echo "Copiaría archivos a servidor Airflow aquí"
    - echo "scp -r dags/* airflow@prod-server:/opt/airflow/dags/"
    - echo "✓ DAGs desplegados"
  only:
    - main
  when: manual
  environment:
    name: production
    deployment_tier: production
```

### Paso 3.4: Commit y push

```bash
cd ~/formacion-cd/airflow-dags
git add .
git commit -m "Add CI/CD pipeline for DAGs"
git config user.email "student@training"
git config user.name "Student"
git push -u origin main
```

### Paso 3.5: Ver pipeline en GitLab

1. Proyecto → "CI/CD" → "Pipelines"
2. Nueva pipeline debería estar ejecutándose

Click para ver detalles.

### Paso 3.6: Ejecutar stages

1. `validate_syntax` - automático
2. `test_dags` - automático
3. `deploy_dags` - manual (click play)

---

## Fase 4: Workflow completo (5 min)

### Paso 4.1: Flujo en Jenkins

```
1. Developer: git push a rama feature
2. Jenkins: Poll SCM detecta cambio (cada 5 min)
3. Jenkins: Valida syntax
4. Jenkins: Ejecuta tests
5. Si OK: Deploy DAGs
6. Si OK: Scheduler rescaneae
7. Resultado: Nuevo DAG vivo en Airflow
```

### Paso 4.2: Flujo en GitLab

```
1. Developer: git push a rama develop
2. GitLab: Webhook detecta cambio (instantáneo)
3. GitLab CI: Valida syntax
4. GitLab CI: Ejecuta tests
5. Developer: Merge request a main
6. GitLab CI: Deploy DAGs (manual)
7. Resultado: Nuevo DAG vivo en Airflow
```

---

## Fase 5: Crear DAG nuevo y deployer (10 min, opcional)

### Paso 5.1: Crear nuevo DAG

**dags/sensor_file_dag.py:**

```python
#!/usr/bin/env python3
"""
DAG con sensor: espera archivo, luego procesa.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'sensor_procesar_archivo',
    default_args=default_args,
    schedule_interval=None,  # Manual
    start_date=datetime(2024, 1, 1),
    tags=['sensor']
)

def procesar():
    print("✓ Archivo detectado y procesado")

# Task 1: Esperar archivo
wait_file = FileSensor(
    task_id='esperar_archivo_entrada',
    filepath='/opt/airflow/data/entrada.txt',
    fs_conn_id='fs_default',
    timeout=60,
    mode='poke',
    dag=dag
)

# Task 2: Procesar
process = PythonOperator(
    task_id='procesar_archivo',
    python_callable=procesar,
    dag=dag
)

wait_file >> process
```

### Paso 5.2: Commit y push

```bash
cd ~/formacion-cd/airflow-dags  # o ~/formacion-cd/airflow si Jenkins

git add dags/sensor_file_dag.py
git commit -m "Add new DAG: sensor_procesar_archivo"
git push
```

### Paso 5.3: Ver pipeline ejecutarse

**Jenkins:** esperar 5 minutos o triggear manualmente

**GitLab:** automático

Tests deberían pasar. Deploy si es main.

### Paso 5.4: Verificar DAG en Airflow

1. Airflow UI: `http://localhost:8080`
2. Esperar ~30 segundos
3. "DAGs" list debe mostrar `sensor_procesar_archivo`

---

## Troubleshooting

### ❌ Error: "pytest not found"

**Solución:**

```bash
pip install pytest apache-airflow
```

### ❌ Error: "Test fails: expected 4 tasks, got 3"

**Solución:** Por cada nuevo DAG, actualizar tests si tiene número diferente de tasks.

### ❌ Error: "DAG not appearing en Airflow"

**Solución:** Esperar 30-60 segundos. Scheduler rescaneaevery 30 seg.

O reiniciar scheduler:

```bash
docker-compose restart airflow-scheduler
```

### ❌ Error: "SCP: No such file or directory"

**Solución:** En demo, Deploy stage no hace nada real. En producción, configurar SSH key, hostname, path.

---

## Best Practices

✅ **DO:**
- ✅ Test DAGs antes de deploy.
- ✅ Mirroring de datos para tests (CSV, tablas).
- ✅ Versionado de DAGs (tags, semver).
- ✅ Alerts si pipeline falla.

❌ **DON'T:**
- ❌ Deployar sin tests.
- ❌ Modificar DAGs en servidor directamente.
- ❌ Credenciales hardcodeadas en DAGs.

---

## Validación Final

**Checklist:**

- [ ] Tests creados para DAG existente
- [ ] Pytest ejecutado localmente sin errores
- [ ] Pipeline Jenkins creada
- [ ] Jenkins valida syntax automáticamente
- [ ] Jenkins ejecuta tests automáticamente
- [ ] GitLab CI `.gitlab-ci.yml` creado
- [ ] Pipeline GitLab ejecuta tests
- [ ] Nuevo DAG creado
- [ ] Nuevo DAG pasa tests
- [ ] Nuevo DAG aparece en Airflow después de deploy

---

## Resumen

Acabas de implementar **CI/CD para orquestación**.

```
DAG nuevo → Commit → Pipeline CI → Tests → Deploy automático → Vivo
```

Esto acelera desarrollo de workflows Big Data, con garantía de calidad.

Sin CI/CD: cambios manuales, frágiles, lentos.  
Con CI/CD: cambios automáticos, validados, rápidos.
