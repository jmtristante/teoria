# Práctica 6.1: Introducción a Apache Airflow

**Duración estimada:** 60 minutos  
**Requisitos previos:** Docker, docker-compose. Módulos 3-5 completados.

---

## Objetivo

Instalar Apache Airflow con docker-compose y crear un DAG simple de ETL:
1. Extract: leer archivo CSV
2. Transform: validar datos
3. Load: guardar resultado en base de datos

---

## Fase 1: Preparar estructura (5 min)

### Paso 1.1: Crear directorio

```bash
mkdir -p ~/formacion-cd/airflow && cd ~/formacion-cd/airflow
mkdir -p dags logs plugins
```

### Paso 1.2: Crear máscara de permisos

```bash
chmod -R 777 dags logs plugins
```

Airflow necesita escribir en estas carpetas desde container.

---

## Fase 2: Docker Compose (10 min)

### Paso 2.1: Crear docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      timeout: 5s
      retries: 5

  airflow-webserver:
    image: apache/airflow:2.7.0-python3.11
    environment:
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'False'
      AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS: 'False'
      PYTHONPATH: /opt/airflow
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./data:/opt/airflow/data
    command: >
      bash -c "
      airflow db init &&
      airflow users create \
        --username admin \
        --password admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com 2>/dev/null || true &&
      airflow webserver
      "
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  airflow-scheduler:
    image: apache/airflow:2.7.0-python3.11
    environment:
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: 'False'
      PYTHONPATH: /opt/airflow
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./data:/opt/airflow/data
    command: airflow scheduler
    depends_on:
      postgres:
        condition: service_healthy
      airflow-webserver:
        condition: service_healthy

volumes:
  postgres_data:

networks:
  default:
    name: airflow-network
```

---

## Fase 3: Iniciar Airflow (10 min)

### Paso 3.1: Levantar stack

```bash
cd ~/formacion-cd/airflow
docker-compose up -d
```

Espera ~30 segundos a que inicialice.

### Paso 3.2: Verificar servicios

```bash
docker-compose ps
```

Deberías ver:

```
NAME                  COMMAND              STATUS
airflow-postgres-1    postgres             Up (healthy)
airflow-webserver-1   webserver            Up (healthy)
airflow-scheduler-1   scheduler            Up (healthy)
```

### Paso 3.3: Abrir UI

Navegador: `http://localhost:8080`

Login:
- Usuario: `admin`
- Password: `admin`

Deberías ver dashboard vacío (sin DAGs aún).

### ✓ Checkpoint 1: Airflow corriendo

---

## Fase 4: Crear Datos de Prueba (5 min)

### Paso 4.1: Crear CSV

```bash
mkdir -p ~/formacion-cd/airflow/data
cd ~/formacion-cd/airflow/data
```

**usuarios.csv:**

```csv
id,nombre,email,edad
1,Juan,juan@example.com,28
2,Maria,maria@example.com,32
3,Carlos,carlos@example.com,25
4,Ana,ana@example.com,invalid_age
5,Luis,luis@example.com,35
```

(Nota: fila 4 tiene edad inválida para demostrar validación.)

### Paso 4.2: Crear tabla en PostgreSQL

```bash
docker-compose exec postgres psql -U airflow -d airflow -c "
CREATE TABLE IF NOT EXISTS usuarios_procesados (
    id INT,
    nombre VARCHAR(100),
    email VARCHAR(100),
    edad INT,
    procesado_en TIMESTAMP DEFAULT NOW()
);
"
```

---

## Fase 5: Crear primer DAG (20 min)

### Paso 5.1: Crear DAG file

**dags/etl_usuarios_dag.py:**

```python
#!/usr/bin/env python3
"""
DAG simple: Extrae CSV, valida, carga a PostgreSQL.
"""
from datetime import datetime, timedelta
import pandas as pd
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

# Argumentos por defecto
default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Definir DAG
dag = DAG(
    "etl_usuarios",
    default_args=default_args,
    schedule="@daily",   # antes: schedule_interval='@daily'
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "usuarios"],
)

# Task 1: Extract (leer CSV)
def extract_usuarios():
    """Extrae usuarios de CSV."""
    print("=== EXTRACT ===")
    df = pd.read_csv('/opt/airflow/data/usuarios.csv')
    print(f"✓ Leídos {len(df)} usuarios")
    print(df.head())
    
    # Guardar para siguiente task (XCom)
    return df.to_json()

task_extract = PythonOperator(
    task_id='extract_usuarios',
    python_callable=extract_usuarios,
    dag=dag
)

# Task 2: Transform (validar)
def transform_usuarios(ti):
    """Valida y transforma datos."""
    print("=== TRANSFORM ===")

    df_json = ti.xcom_pull(task_ids='extract_usuarios')
    df = pd.read_json(df_json)

    print(f"✓ Recibidos {len(df)} usuarios")

    # Convertir edad a número; lo inválido pasa a NaN
    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')

    # Validación: edad entre 18 y 100
    mask_valido = df['edad'].between(18, 100, inclusive='both')
    df_valido = df[mask_valido].copy()

    print(f"✓ Validados {len(df_valido)} usuarios (rechazados {len(df) - len(df_valido)})")

    rechazados = df[~mask_valido]
    if len(rechazados) > 0:
        print("⚠ Usuarios inválidos:")
        print(rechazados)

    return df_valido.to_json()

task_transform = PythonOperator(
    task_id='transform_usuarios',
    python_callable=transform_usuarios,
    dag=dag
)

# Task 3: Load (guardar en DB)
def load_usuarios(ti):
    """Carga usuarios válidos a PostgreSQL."""
    print("=== LOAD ===")
    import psycopg2
    
    # Obtener resultado de transform
    df_json = ti.xcom_pull(task_ids='transform_usuarios')
    df = pd.read_json(df_json)
    
    print(f"✓ Cargando {len(df)} usuarios a PostgreSQL")
    
    # Conectar a PostgreSQL
    conn = psycopg2.connect(
        host='postgres',
        user='airflow',
        password='airflow',
        database='airflow'
    )
    cursor = conn.cursor()
    
    # Insertar
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO usuarios_procesados (id, nombre, email, edad)
            VALUES (%s, %s, %s, %s)
        ''', (row['id'], row['nombre'], row['email'], row['edad']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ {len(df)} usuarios insertados")

task_load = PythonOperator(
    task_id='load_usuarios',
    python_callable=load_usuarios,
    dag=dag
)

# Task 4: Validación post-load
def validate_load():
    """Verifica que datos se cargaron correctamente."""
    print("=== VALIDATE ===")
    import psycopg2
    
    conn = psycopg2.connect(
        host='postgres',
        user='airflow',
        password='airflow',
        database='airflow'
    )
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM usuarios_procesados;')
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print(f"✓ Total usuarios en DB: {count}")
    print("✓ ETL completado exitosamente")

task_validate = PythonOperator(
    task_id='validate_load',
    python_callable=validate_load,
    dag=dag
)

# Dependencias
task_extract >> task_transform >> task_load >> task_validate
```

### Paso 5.2: Instalar dependencias en container

```bash
docker-compose exec airflow-webserver pip install pandas psycopg2-binary
```

### Paso 5.3: Recargar Airflow

```bash
docker-compose restart airflow-webserver airflow-scheduler
```

Espera 30 segundos.

---

## Fase 6: Ejecutar el DAG (15 min)

### Paso 6.1: Verificar DAG en UI

1. `http://localhost:8080`
2. "DAGs" → buscar `etl_usuarios`
3. Debería aparecer en la lista

Nota: si no aparece, espera 1 minuto más (scheduler reescaneaevery 30 segundos).

### Paso 6.2: Ver estructura del DAG

Click en `etl_usuarios` → "Graph View"

Deberías ver:

```
extract_usuarios → transform_usuarios → load_usuarios → validate_load
```

### Paso 6.3: Ejecutar DAG manualmente

En "DAGs" list, click ▶ (play) en `etl_usuarios`

O en DAG details, click "Trigger DAG"

### Paso 6.4: Monitorear ejecución

Click en "Tree View" o "Graph View" para ver estado.

Estados posibles:
- **Queued:** esperando ejecutar
- **Running:** ejecutando ahora
- **Success:** completado exitosamente
- **Failed:** error

### Paso 6.5: Ver logs

Click en cada task → "View Logs"

Deberías ver logs de cada etapa:

```
=== EXTRACT ===
✓ Leídos 5 usuarios
...

=== TRANSFORM ===
✓ Recibidos 5 usuarios
✓ Validados 4 usuarios (rechazados 1)
⚠ Usuarios inválidos:
   id    nombre            email           edad
4   4      Ana  ana@example.com           NaN
...

=== LOAD ===
✓ Cargando 4 usuarios a PostgreSQL
✓ 4 usuarios insertados
...

=== VALIDATE ===
✓ Total usuarios en DB: 4
✓ ETL completado exitosamente
```

### ✓ Checkpoint 2: DAG ejecutado exitosamente

---

## Fase 7: Explorar UI (10 min)

### Paso 7.1: Entender Tree View

"Tree View" muestra:

```
etl_usuarios  [día 1] [día 2] [día 3] ...
├─ extract    Success Success Success
├─ transform  Success Success Success
├─ load       Success Success Success
└─ validate   Success Success Failed
```

Cada columna = una ejecución del DAG.

Click en cualquier cell para ver detalles/logs.

### Paso 7.2: Entender Graph View

"Graph View" muestra estructura del workflow:

```
┌────────────┐     ┌──────────────┐     ┌──────────┐     ┌───────────┐
│   extract  │────▶│  transform   │────▶│   load   │────▶│ validate  │
└────────────┘     └──────────────┘     └──────────┘     └───────────┘
    0.5s              0.8s                 1.2s             0.3s
```

Duración de cada task mostrada.

### Paso 7.3: Variables de Airflow (Jinja)

En DAGs, puedes usar variables:

```python
bash_command='echo "Run date: {{ ds }}"'  # ds = date string (YYYY-MM-DD)
bash_command='echo "Exec date: {{ execution_date }}"'
```

### Paso 7.4: Ver conexiones

"Admin" → "Connections"

Aquí se guardan credenciales para Spark, PostgreSQL, etc. (no hardcodeadas).

---

## Fase 8: Crear segundo DAG con Retry (10 min)

### Paso 8.1: DAG con fallo simulado

**dags/etl_con_retry_dag.py:**

```python
#!/usr/bin/env python3
"""
DAG que demuestra retries automáticos.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(seconds=10),
}

dag = DAG(
    'etl_con_retry',
    default_args=default_args,
    schedule_interval=None,  # Manual trigger solo
    start_date=datetime(2024, 1, 1),
    tags=['etl', 'retry-demo']
)

# Contador simulado de fallos
attempt = {'count': 0}

def task_que_falla():
    """Falla 2 veces, luego success."""
    attempt['count'] += 1
    print(f"Intento #{attempt['count']}")
    
    if attempt['count'] < 3:
        raise Exception(f"Fallo intento {attempt['count']} - reintentaremos en 10 segundos")
    else:
        print("✓ Success en intento 3!")

task = PythonOperator(
    task_id='fallo_y_retry',
    python_callable=task_que_falla,
    dag=dag
)
```

### Paso 8.2: Deploy y ejecutar

```bash
docker-compose restart airflow-scheduler
```

Espera 30 segundos.

En UI:
1. "DAGs" → `etl_con_retry`
2. Trigger DAG

Ver logs para ver 3 intentos (fallo, retry, retry, success).

---

## Troubleshooting

### ❌ Error: "DAG not appearing in UI"

**Solución:** Scheduler necesita reescaneaer dags/. Espera 30-60 segundos.

Si persiste:

```bash
docker-compose logs airflow-scheduler | tail -50
```

### ❌ Error: "ImportError: No module named pandas"

**Solución:** Instalar en container:

```bash
docker-compose exec airflow-webserver pip install pandas psycopg2-binary
docker-compose restart
```

### ❌ Error: "Connection refused: postgres"

**Solución:** PostgreSQL no está listo. Esperar:

```bash
docker-compose ps  # Ver si postgres está healthy
```

o reiniciar:

```bash
docker-compose restart postgres
```

### ❌ Error: "Table does not exist"

**Solución:** Volver a crear:

```bash
docker-compose exec postgres psql -U airflow -d airflow -c "DROP TABLE usuarios_procesados; CREATE TABLE usuarios_procesados (...);"
```

---

## Validación Final

**Checklist:**

- [ ] Docker-compose levantado (3 servicios: postgres, webserver, scheduler)
- [ ] UI accesible en http://localhost:8080
- [ ] DAG `etl_usuarios` visible en UI
- [ ] Graph View muestra 4 tasks conectados
- [ ] DAG ejecutado manualmente sin errores
- [ ] Logs visibles para cada task
- [ ] PostgreSQL contiene 4 usuarios (1 rechazado)
- [ ] Segundo DAG con retries crea
- [ ] Entiendes diferencia entre task, operator, DAG, execution

---

## Conceptos Clave

1. **DAG:** archivo Python que define workflow.
2. **Operator:** tipo de task (PythonOperator, BashOperator, etc.).
3. **Task:** instancia específica de un operator.
4. **XCom:** paso de datos entre tasks (`xcom_pull`, `xcom_push`).
5. **Dependencias:** orden de ejecución (usar `>>`).
6. **Retries:** automático si falla.
7. **Scheduling:** cron + templates Jinja (`{{ ds }}`).

---

## Extensiones Opcionales

1. **Agregar email alerts:** si DAG falla, enviar email.
2. **SparkOperator:** ejecutar job PySpark.
3. **Sensor:** esperar archivo, base de datos, etc.
4. **Backfilling:** `airflow dags backfill -d etl_usuarios --start-date 2024-01-01`
5. **Variables de Airflow:** guardar valores reutilizables en UI.
