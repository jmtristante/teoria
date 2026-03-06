# Módulo 6: Apache Airflow y CI/CD

**Duración:** 2.5h  
**Público:** Desarrolladores de Big Data en formación

---

## Introducción: ¿Por qué Airflow?

Hasta ahora hemos aprendido CI/CD: cómo deployar aplicaciones automáticamente.

Pero en Big Data, no solo desplegamos aplicaciones. **Orquestamos workflows**.

Imagina este escenario:

> "Todos los días a las 6 AM, necesito:
> 1. Extraer datos de 3 fuentes diferentes (API, S3, base de datos).
> 2. Transformar cada una en paralelo (30% del trabajo).
> 3. Combinar las 3 transformadas (esperar a que todas terminen).
> 4. Cargar resultado a warehouse (5 minutos después de 3.).
> 5. Enviar email si algo falla.
> 6. Registrar reporte diario si todo OK.
> 7. Si hay error en paso 2, reintentar 3 veces. Si sigue fallando, alertar.
> 8. Si la carga toma más de 30 minutos, timeout y rollback."

Esto es orquestación: muchos **tasks** con **dependencias complejas**, **logs**, **retries**, **monitoring**.

Un script Bash con `cron` se vuelve un desastre. Un comando Python con sleeps es frágil.

**Apache Airflow** es la solución: orquestador de workflows open-source para Big Data.

---

## 6.1 Conceptos Fundamentales

### ¿Qué es Apache Airflow?

Airflow es una **plataforma de orquestación** (schedulea y monitoriza workflows complejos).

Características clave:

1. **DAGs (Directed Acyclic Graphs):** se define el workflow como código (Python).
2. **Scheduling:** ejecuta automáticamente en horarios específicos (cron).
3. **Retry & Recovery:** si un task falla, reintentar automáticamente.
4. **Monitoring:** UI web para ver estado de execuciones, logs, dependencias.
5. **Operators:** bloques reutilizables (BashOperator, PythonOperator, SparkOperator, etc.).
6. **Backfilling:** ejecutar DAG atrasado para llenar datos históricos.

### DAG: Directed Acyclic Graph

Un DAG es un **grafo de tareas con direcciones acíclicas**.

```
Estructura:

        API Extract → Transform A ┐
                                   ├→ Combine → Load → Email
        DB Extract  → Transform B ┤
                                   ┘
        S3 Extract  → Transform C ┘
```

Términos:

- **Task:** unidad de trabajo (extract, transform, load, notify).
- **Operator:** tipo de task (PythonOperator ejecuta función Python, BashOperator ejecuta script bash).
- **Dependencia:** orden de ejecución (Task A antes que Task B).
- **DAG:** colección de tasks con dependencias. **Acíclico = sin loops.**

### Operators: Los bloques de construcción

Imagine operators como "rompecabezas de trabajo":

| Operator | Para qué | Ejemplo |
|----------|----------|---------|
| `PythonOperator` | Ejecutar función Python | Transformar datos con pandas |
| `BashOperator` | Ejecutar comando shell | `spark-submit job.py` |
| `SparkOperator` | Submeter job a Spark cluster | PySpark ETL |
| `PostgresOperator` | Ejecutar query SQL | INSERT/UPDATE/DELETE |
| `S3Operator` | Interactuar con S3 | Upload, download, list |
| `SensorOperator` | Esperar condición (archivo, base de datos, tiempo) | Esperar a que aparezca archivo en S3 |
| `EmailOperator` | Enviar email | Notificar al finalizar |

Un DAG es básicamente: "elige operators, conecta dependencias, scheduling".

### Scheduling: "Cuándo" ejecutar

```python
dag = DAG(
    'daily_etl',
    schedule_interval='0 6 * * *',  # Cron: 6 AM todos los días
    start_date=datetime(2024, 1, 1),
    catchup=False
)
```

**Cron cheatsheet:**

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ Día semana (0=domingo)
│ │ │ └─── Mes (1-12)
│ │ └───── Día mes (1-31)
│ └─────── Hora (0-23)
└───────── Minuto (0-59)

Ejemplos:
0 6 * * *     = 6 AM todos los días
0 */4 * * *   = Cada 4 horas
30 9 * * 1-5  = 9:30 AM lunes-viernes
```

### Retry & Recovery

Si un task falla, Airflow puede reintentar automáticamente:

```python
default_args = {
    'retries': 3,                # Reintentar 3 veces
    'retry_delay': timedelta(minutes=5),  # Esperar 5 min entre intentos
}

task = PythonOperator(
    task_id='risky_task',
    python_callable=my_function,
    **default_args
)
```

Si falla tras 3 reintentos, marca task como FAILED y ejecuta `on_failure_callback` (por ejemplo, enviar email).

### Backfilling: Rellenar datos históricos

Imagina que tu DAG comenzó el 2024-01-01, pero hoy es 2024-03-06 y necesitas ejecutar 64 días históricos.

```bash
airflow dags backfill --dag-id daily_etl --start-date 2024-01-01 --end-date 2024-03-06
```

Airflow ejecuta el DAG para cada día, en paralelo (si hay workers disponibles).

---

## 6.2 Monitoreo y Logs

### UI de Airflow

La web UI (`http://localhost:8080` típicamente) muestra:

1. **DAG List:** qué DAGs existen.
2. **DAG Details:** tasks, dependencias, historial de execuciones.
3. **Tree View:** visualiza cronología de runs.
4. **Graph View:** visualiza estructura de tasks (el DAG dibujado).
5. **Logs:** output de cada task.
6. **XComs:** comunicación entre tasks (Task A → Task B: "aquí está el resultado").

### Logs Centralizados

Cada task genera logs. Airflow guarda en:

```
logs/
├── daily_etl/
│   ├── extract_api/
│   │   ├── 2024-03-06T06:00:00+00:00/
│   │   └── 2024-03-05T06:00:00+00:00/
│   └── load_warehouse/
```

En UI, click en task → ver logs en tiempo real.

### XComs: Comunicación entre Tasks

A veces, un task necesita resultado de otro (Task A extrae número de filas, Task B lo necesita).

```python
# Task A: extrae y pushea dato
def extract_data():
    return {'rows': 1000}

task_a = PythonOperator(
    task_id='extract',
    python_callable=extract_data
)

# Task B: obtiene resultado de A
def load_data(ti):  # ti = Task Instance
    value = ti.xcom_pull(task_ids='extract')
    print(f"Rows to load: {value['rows']}")

task_b = PythonOperator(
    task_id='load',
    python_callable=load_data
)

task_a >> task_b  # A ejecuta primero
```

---

## 6.3 Instalación y Setup

### Docker Compose Simplificado

En producción, Airflow es complejo (scheduler, webserver, workers, database, message broker).

Para formación, usamos simplificado:

```yaml
version: '3'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: airflow
      POSTGRES_USER: airflow
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"

  airflow-webserver:
    image: apache/airflow:2.7.0-python3.11
    environment:
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
    command: bash -c "airflow db init && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com 2>/dev/null || true && airflow webserver"
    depends_on:
      - postgres

  airflow-scheduler:
    image: apache/airflow:2.7.0-python3.11
    environment:
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
    volumes:
      - ./dags:/opt/airflow/dags
    command: airflow scheduler
    depends_on:
      - postgres
      - airflow-webserver
```

### Carpeta DAGs

Los DAGs se colocan en carpeta `dags/`:

```
airflow-docker/
├── docker-compose.yml
├── dags/
│   ├── daily_etl.py
│   ├── hourly_reporting.py
│   └── weekly_cleanup.py
```

Airflow escanea cada 30 segundos. Si ves nuevo DAG en UI, está listo.

---

## 6.4 Ejemplo DAG Simple

```python
# dags/hello_world.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Argumentos por defecto
default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definir DAG
dag = DAG(
    'hello_world',
    default_args=default_args,
    schedule_interval='0 6 * * *',  # 6 AM todos los días
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['tutorial', 'simple']
)

# Task 1: Python
def say_hello():
    print("✓ Hello from Airflow!")

task_hello = PythonOperator(
    task_id='hello',
    python_callable=say_hello,
    dag=dag
)

# Task 2: Bash
task_date = BashOperator(
    task_id='print_date',
    bash_command='echo "Execution date: {{ ds }}"',
    dag=dag
)

# Task 3: Python con delay
def sleep_task():
    import time
    print("Waiting...")
    time.sleep(5)
    print("Done!")

task_sleep = PythonOperator(
    task_id='sleep',
    python_callable=sleep_task,
    dag=dag
)

# Dependencias
task_hello >> task_date >> task_sleep
```

Flujo:
1. `hello` → imprime "Hello"
2. `print_date` → imprime fecha
3. `sleep` → espera 5 seg
4. Finaliza

---

## 6.5 CI/CD para DAGs

### El Problema: Deployar DAGs Nuevos

Desarrollo de Data Engineer:

```
1. Escribo DAG localmente
2. Testeo en Airflow local
3. Hago push a Git
4. Necesito copiar a carpeta DAGs del servidor Airflow
```

Sin CI/CD: manual y propenso a errores.

Con CI/CD:

```
Git push → Pipeline detecta cambio en dags/ → 
→ Tests corren → DAG se copia a servidor → 
→ Airflow rescana automáticamente → ¡DAG vivo!
```

### Testing DAGs

**¿Qué se testea?**

1. **Estructura:** DAG es válido (parámetros, dependencias, no hay ciclos).
2. **Imports:** todos los módulos importados existen (no hay typos en operators).
3. **Lógica:** la función Python de cada task funciona.

**Ejemplo: Test estructura DAG**

```python
# tests/test_hello_world_dag.py
import pytest
from dags.hello_world import dag

def test_dag_loads():
    """Validar que DAG carga sin errores."""
    assert dag is not None

def test_dag_has_tasks():
    """Validar que DAG tiene tasks."""
    assert len(dag.tasks) == 3

def test_task_dependencies():
    """Validar dependencias."""
    # Task 1 debe ejecutar primero
    task_hello = dag.tasks_dict['hello']
    task_date = dag.tasks_dict['print_date']
    
    assert task_date in task_hello.downstream_list
```

### Deployment de DAG Automático

Pipeline Git:

```yaml
# .gitlab-ci.yml para Airflow
stages:
  - test
  - deploy

test_dags:
  stage: test
  image: python:3.11
  script:
    - pip install apache-airflow pytest
    - pytest tests/ -v
    - python -m py_compile dags/*.py  # Validar syntax

deploy_dag:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H $AIRFLOW_SERVER >> ~/.ssh/known_hosts
    - scp -r dags/* $AIRFLOW_USER@$AIRFLOW_SERVER:/opt/airflow/dags/
    - echo "✓ DAGs deployed"
  only:
    - main
  when: manual
```

Variables necesarias:
- `SSH_PRIVATE_KEY`: key privada para SSH
- `AIRFLOW_SERVER`: IP/hostname del servidor Airflow
- `AIRFLOW_USER`: usuario SSH

---

## 6.6 Comparación: Airflow vs Cron vs Scripts

| Aspecto | Cron | Script manual | Airflow |
|---------|------|--------------|---------|
| Definición | Línea en crontab | Script Bash/Python | DAG en Python |
| Retries | No | Manual | Automático |
| Monitoring | Email si falla | Ninguno | Web UI, logs, alertas |
| Dependencias | Difícil (if/sleep) | Manual | Declarativo |
| Backfilling | No | Manual | Automático |
| Escalabilidad | Una máquina | Complicado | Workers distribuidos |
| Logs centralizados | No | No | Sí |

### Cuándo usar Airflow

✅ **Usa Airflow si:**

- Workflow con **múltiples tasks interdependientes**.
- Necesitas **retries automáticos** y **recovery**.
- Requieres **logs centralizados** y **monitoring**.
- Cambios frecuentes en **lógica del workflow**.
- Necesitas **backfilling histórico**.

❌ **No necesitas Airflow si:**

- Un único script que corre diariamente (cron alcanza).
- No hay dependencias entre tasks.
- No necesitas monitoring sofisticado.

---

## 6.7 Big Data + Airflow

### Casos de uso típicos

1. **ETL diario:** Extract datos, Transform, Load warehouse.

```python
extract_api >> extract_db >> extract_s3 >> transform >> load_warehouse >> quality_check
```

2. **Data pipeline con Spark:** orquestar múltiples jobs Spark.

```python
spark_clean >> spark_aggregate >> spark_report >> email_report
```

3. **Backfill histórico:** procesar 5 años de datos en paralelo.

```bash
airflow dags backfill --dag-id daily_etl --start-date 2019-01-01 --end-date 2024-03-06
```

4. **Sensor + Trigger:** espera archivo, entonces procesa.

```python
wait_for_file_sensor >> process_file >> upload_results
```

### Airflow en Producción (Big Picture)

```
┌─────────────┐
│ Git Repo    │
│  (DAGs)     │
└──────┬──────┘
       │ (push)
       ▼
┌──────────────────┐
│  Pipeline CI/CD  │  ← Test, validate
└──────┬───────────┘
       │ (deploy)
       ▼
┌──────────────────────────────────┐
│   Airflow Scheduler + Webserver  │
│   + Workers + Database           │
└──────┬───────────────────────────┘
       │ (ejecuta DAGs en schedule)
       ▼
┌──────────────────┐
│  Data Platform   │
│  (Spark, Kafka,  │
│   S3, DB, etc)   │
└──────────────────┘
```

---

## Resumen de Conceptos Clave

1. **DAG:** grafo de tasks con dependencias (sin ciclos).
2. **Operators:** bloques reutilizables (Python, Bash, Spark, SQL, etc.).
3. **Scheduling:** Cron para "cuándo" (6 AM, cada hora, etc.).
4. **Retries:** automático si falla.
5. **Monitoring:** UI web para logs y estado.
6. **XComs:** paso de datos entre tasks.
7. **Backfilling:** ejecutar DAG atrasado para datos históricos.
8. **CI/CD para DAGs:** tests + deploy automático.

---

## Próximo: Práctica 6.1

En la próctica, instalarás Airflow con docker-compose e implementarás tu primer DAG ETL completo.
