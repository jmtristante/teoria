# Módulo 7: Monitorización Básica

**Duración:** 1.5h  
**Público:** Desarrolladores de Big Data en formación

---

## Introducción: ¿Por qué Monitorizar?

Has aprendido a construir pipelines CI/CD completas:
- Código se testea automáticamente.
- Artefactos se empaquetan con Docker.
- Deployments ocurren en dev/test/prod.
- Airflow orquesta workflows complejos.

Pero... **¿qué pasa después del deploy?**

Imagina estos escenarios:

> **Escenario 1:** Tu pipeline desplegó la aplicación a las 6 AM. A las 8 AM, usuarios reportan que el servicio no responde. ¿Cuándo falló exactamente? ¿Por qué?

> **Escenario 2:** Un DAG de Airflow corre cada hora. A veces tarda 5 minutos, otras veces 45 minutos. Hoy tardó 2 horas y nadie se dio cuenta hasta el día siguiente.

> **Escenario 3:** Tu aplicación procesa 1000 registros por segundo normalmente. Hoy procesó solo 100 por segundo. ¿Qué cambió? ¿Fue el deploy de ayer?

Sin monitorización, estos problemas son **invisibles hasta que alguien se queja**.

Con monitorización:
- **Logs:** sabes qué pasó y cuándo.
- **Health checks:** detectas fallos inmediatamente.
- **Métricas:** ves degradación de performance antes de que cause incidentes.
- **Alertas:** recibes notificación automática si algo va mal.

Este módulo cubre **monitorización básica** (no herramientas complejas tipo Prometheus/Grafana, sino lo esencial para empezar).

---

## 7.1 Logs: El Diario de tu Aplicación

### ¿Qué son los Logs?

Logs son **mensajes que tu aplicación genera mientras corre**.

Ejemplos:

```
2024-03-06 08:15:23 INFO - Starting ETL job
2024-03-06 08:15:24 INFO - Connected to database: prod-db.internal
2024-03-06 08:15:27 INFO - Extracted 10000 rows from source
2024-03-06 08:15:35 WARNING - Row 4532 has invalid email, skipping
2024-03-06 08:16:12 INFO - Transformation completed: 9999 valid rows
2024-03-06 08:16:15 ERROR - Failed to connect to target DB: timeout after 5s
2024-03-06 08:16:20 INFO - Retrying connection (attempt 2/3)
2024-03-06 08:16:25 INFO - Connection successful
2024-03-06 08:18:45 INFO - Loaded 9999 rows to warehouse
2024-03-06 08:18:46 INFO - ETL job completed successfully
```

Con estos logs, sabes:
- Cuándo empezó (08:15:23).
- Cuántos datos procesó (10000 → 9999).
- Qué problema hubo (timeout DB en 08:16:15).
- Cuánto tardó (3 minutos 23 segundos).

Sin logs: "algo falló", pero no sabes qué, cuándo, ni por qué.

### Niveles de Log

Los logs tienen **niveles de severidad**:

| Nivel | Uso | Ejemplo |
|-------|-----|---------|
| **DEBUG** | Detalle extremo (desarrollo) | `"Variable x = 42"`, `"Iterating row 1523"` |
| **INFO** | Eventos normales | `"Job started"`, `"Connected to DB"`, `"Processed 1000 rows"` |
| **WARNING** | Algo raro pero no fatal | `"Retrying after timeout"`, `"Row invalid, skipping"` |
| **ERROR** | Error que impide operación | `"Failed to connect DB"`, `"File not found"` |
| **CRITICAL** | Error catastrófico | `"Database corrupted"`, `"Out of memory"` |

En **desarrollo:** DEBUG + INFO (ves todo).  
En **producción:** INFO + WARNING + ERROR (solo lo relevante).

### Logs Estructurados vs. No Estructurados

**No estructurado (texto plano):**

```
App started
User logged in
Error: timeout
```

Difícil de parsear automáticamente.

**Estructurado (JSON):**

```json
{"timestamp": "2024-03-06T08:15:23Z", "level": "INFO", "message": "App started"}
{"timestamp": "2024-03-06T08:15:25Z", "level": "INFO", "message": "User logged in", "user_id": 42}
{"timestamp": "2024-03-06T08:16:15Z", "level": "ERROR", "message": "Timeout", "service": "database", "duration_ms": 5000}
```

Ventajas:
- **Parseaable:** herramientas pueden buscar, filtrar, agregar.
- **Traceable:** puedes seguir `user_id` a través de múltiples logs.
- **Métricas:** extraer `duration_ms` para análisis.

### Implementar Logging en Python

**Sin logging (malo):**

```python
print("Starting job")
print("Processing data")
# Sin contexto, no hay timestamp, no hay niveles
```

**Con logging (correcto):**

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Usar en código
logger.info("Starting ETL job")
logger.debug(f"Processing row {row_id}")
logger.warning(f"Row {row_id} has invalid data, skipping")
logger.error(f"Failed to connect DB: {error}")
```

Output:

```
2024-03-06 08:15:23,456 - __main__ - INFO - Starting ETL job
2024-03-06 08:15:24,123 - __main__ - WARNING - Row 4532 has invalid data, skipping
2024-03-06 08:16:15,789 - __main__ - ERROR - Failed to connect DB: Timeout
```

### Logging Estructurado en Python

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter que output JSON."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_data)

# Configurar
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usar
logger.info("ETL started")
logger.error("Database timeout")
```

Output:

```json
{"timestamp": "2024-03-06T08:15:23.456Z", "level": "INFO", "message": "ETL started", "module": "etl", "function": "main"}
{"timestamp": "2024-03-06T08:16:15.789Z", "level": "ERROR", "message": "Database timeout", "module": "etl", "function": "load_data"}
```

### Logs en Contenedores Docker

Docker captura **stdout y stderr** de cada contenedor.

Ver logs:

```bash
docker logs <container_name>
docker logs -f <container_name>  # Follow en tiempo real
docker logs --tail 50 <container_name>  # Últimas 50 líneas
docker logs --since 5m <container_name>  # Últimos 5 minutos
```

Ejemplo:

```bash
docker logs app-pipeline-prod

# Output:
2024-03-06 08:15:23 INFO - Starting app
2024-03-06 08:15:24 INFO - Connected to DB
2024-03-06 08:16:15 ERROR - Request timeout
```

**Best practice:** tu app debe logear a **stdout** (no a archivos locales). Docker centraliza automáticamente.

---

## 7.2 Health Checks: ¿Está Vivo?

### ¿Qué es un Health Check?

Un health check es un **endpoint HTTP** (o comando) que responde si la aplicación está funcionando correctamente.

Ejemplo:

```
GET http://localhost:5000/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-03-06T08:15:23Z",
  "database": "connected",
  "uptime_seconds": 3600
}
```

Si no responde (timeout) o responde con error → app está rota.

### Health Check en Python (Flask)

```python
from flask import Flask, jsonify
import psycopg2
from datetime import datetime

app = Flask(__name__)
start_time = datetime.now()

@app.route('/health')
def health():
    """Health check endpoint."""
    
    # Check 1: App está corriendo (si llega aquí, sí)
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.now() - start_time).total_seconds()
    }
    
    # Check 2: Base de datos accesible
    try:
        conn = psycopg2.connect(
            host='prod-db',
            user='app',
            password='secret',
            connect_timeout=3
        )
        conn.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "error"
        health_status["database_error"] = str(e)
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503  # Service Unavailable
    
    return jsonify(health_status), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Uso:

```bash
curl http://localhost:5000/health

# Si healthy:
{"status":"healthy","timestamp":"2024-03-06T08:15:23Z","database":"connected","uptime_seconds":3600}
# HTTP 200

# Si unhealthy:
{"status":"unhealthy","timestamp":"2024-03-06T08:16:15Z","database":"error","database_error":"timeout"}
# HTTP 503
```

### Health Check en Dockerfile

Docker puede ejecutar health checks periódicamente:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Health check cada 30 segundos
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
```

Ver estado:

```bash
docker ps

# Columna STATUS muestra:
# Up 5 minutes (healthy)
# Up 5 minutes (unhealthy)
# Up 5 minutes (health: starting)
```

### Health Check en Pipeline CI/CD

Después de deploy, validar que app está healthy:

**Jenkinsfile:**

```groovy
stage('Health Check') {
    steps {
        sh '''
            echo "Waiting for app to start..."
            sleep 10
            
            # Check health endpoint
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
            
            if [ "$HTTP_CODE" -eq 200 ]; then
                echo "✓ App is healthy"
            else
                echo "✗ App is unhealthy (HTTP $HTTP_CODE)"
                exit 1
            fi
        '''
    }
}
```

Si health check falla → pipeline falla → no se completa deploy.

---

## 7.3 Métricas: Números que Importan

### ¿Qué Métricas Monitorizar?

En Big Data + CI/CD, métricas clave:

| Métrica | Qué mide | Ejemplo |
|---------|----------|---------|
| **Latencia** | Tiempo de respuesta | Petición tarda 250ms |
| **Throughput** | Registros/transacciones por segundo | 1000 rows/sec |
| **Error rate** | % de operaciones fallidas | 2% de requests fallan |
| **Uptime** | % de tiempo disponible | 99.5% uptime |
| **CPU/Memory** | Uso de recursos | App usa 80% RAM |
| **Queue size** | Trabajos pendientes | 500 jobs en cola |

### Ejemplo: Contar Operaciones

```python
import logging
from collections import defaultdict

metrics = defaultdict(int)

def process_record(record):
    """Procesa registro y cuenta métricas."""
    try:
        # Lógica de procesamiento
        result = transform(record)
        metrics['records_processed'] += 1
        return result
    except ValueError as e:
        metrics['records_invalid'] += 1
        logging.warning(f"Invalid record: {e}")
        return None
    except Exception as e:
        metrics['records_error'] += 1
        logging.error(f"Error processing record: {e}")
        raise

# Al finalizar job
def print_metrics():
    """Imprime métricas finales."""
    total = sum(metrics.values())
    logging.info(f"=== Metrics ===")
    logging.info(f"Total: {total}")
    logging.info(f"Processed: {metrics['records_processed']}")
    logging.info(f"Invalid: {metrics['records_invalid']}")
    logging.info(f"Errors: {metrics['records_error']}")
    logging.info(f"Success rate: {metrics['records_processed']/total*100:.2f}%")
```

Output:

```
=== Metrics ===
Total: 10000
Processed: 9850
Invalid: 120
Errors: 30
Success rate: 98.50%
```

### Exponer Métricas en Health Check

```python
@app.route('/metrics')
def metrics_endpoint():
    """Endpoint para exponer métricas."""
    return jsonify({
        "records_processed": metrics['records_processed'],
        "records_invalid": metrics['records_invalid'],
        "records_error": metrics['records_error'],
        "success_rate": metrics['records_processed'] / sum(metrics.values()) * 100 if sum(metrics.values()) > 0 else 0
    })
```

Uso:

```bash
curl http://localhost:5000/metrics

{"records_processed":9850,"records_invalid":120,"records_error":30,"success_rate":98.5}
```

---

## 7.4 Alertas: Notificar Cuando Algo Va Mal

### ¿Cuándo Alertar?

No quieres alertas por todo (fatiga de alertas), pero sí por cosas críticas:

✅ **Alertar si:**
- Pipeline falla después de 3 reintentos.
- Health check falla por más de 2 minutos.
- Error rate > 5%.
- Latencia > 10 segundos.
- Disco lleno > 90%.

❌ **No alertar si:**
- Un solo registro es inválido (esperado).
- Request individual tarda 2 segundos (dentro de rango).
- Retry exitoso (se recuperó solo).

### Alertas por Email (Simple)

**Python con smtplib:**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_alert(subject, body):
    """Envía email de alerta."""
    
    sender = "alerts@mycompany.com"
    recipients = ["oncall@mycompany.com"]
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, 'password')
        server.send_message(msg)
        server.quit()
        print("✓ Alert sent")
    except Exception as e:
        print(f"✗ Failed to send alert: {e}")

# Uso
if error_rate > 0.05:
    send_alert(
        subject="[CRITICAL] High error rate detected",
        body=f"Error rate is {error_rate*100:.2f}% (threshold: 5%)"
    )
```

### Alertas en Jenkins Pipeline

```groovy
post {
    failure {
        emailext(
            subject: "[FAILED] Pipeline ${env.JOB_NAME} - Build #${env.BUILD_NUMBER}",
            body: """
                Pipeline failed.
                
                Job: ${env.JOB_NAME}
                Build: ${env.BUILD_NUMBER}
                URL: ${env.BUILD_URL}
                
                Check logs for details.
            """,
            to: 'team@mycompany.com'
        )
    }
}
```

### Alertas en GitLab CI

```yaml
notify_failure:
  stage: notify
  script:
    - |
      curl -X POST https://hooks.slack.com/services/YOUR_WEBHOOK \
        -H 'Content-Type: application/json' \
        -d '{
          "text": "Pipeline failed: '"$CI_PROJECT_NAME"' - '"$CI_PIPELINE_URL"'"
        }'
  when: on_failure
  only:
    - main
```

---

## 7.5 Best Practices de Monitorización

Implementar monitorización efectiva va más allá de simplemente agregar algunas líneas de logging en tu código. Requiere pensar estratégicamente sobre qué información necesitas capturar, cómo organizarla, y cómo evitar que se convierta en ruido inútil. A continuación, exploramos las prácticas fundamentales que te ayudarán a construir un sistema de monitorización robusto y útil.

### Logea Temprano y Frecuentemente (Pero con Criterio)

Uno de los errores más comunes cuando empiezas a trabajar con aplicaciones en producción es no tener suficiente información cuando algo falla. Te encuentras mirando una pantalla vacía preguntándote "¿qué pasó aquí?" sin ninguna pista. La solución es simple: logea los eventos importantes desde el principio.

Cada vez que tu aplicación realiza una acción significativa, debería dejar rastro. Cuando un job de ETL se inicia, cuando se establece una conexión a una base de datos, cuando comienza el procesamiento de un lote de datos, cuando se completa una operación crítica... todos estos son momentos que merecen un log. Piensa en los logs como las migas de pan del cuento de Hansel y Gretel: te permiten reconstruir el camino que siguió tu aplicación hasta llegar a un punto específico.

Sin embargo, logear "todo" no es la respuesta. Hay información que nunca debe aparecer en tus logs. Las contraseñas, tokens de autenticación, claves API y cualquier tipo de credencial deben mantenerse fuera de los logs bajo cualquier circunstancia. Del mismo modo, los datos de identificación personal (PII por sus siglas en inglés) como números de documento, direcciones, o información financiera solo deberían logearse si han sido apropiadamente anonimizados o encriptados. Un log comprometido con esta información puede ser tan peligroso como una brecha de seguridad directa.

### El Contexto es Rey

Imagina que estás revisando los logs de producción a las 3 AM porque algo falló, y te encuentras con esta línea: "Failed". ¿Qué falló? ¿Cuándo? ¿En qué condiciones? Esta es información inútil que solo genera frustración. Ahora compara eso con: "Failed to connect to database prod-analytics-db.region-us-east.internal after 5 seconds timeout on retry attempt 3/5". Ahí tienes una historia completa que te permite actuar inmediatamente.

Cada mensaje de log debería responder las preguntas básicas del periodismo: qué, cuándo, dónde, por qué y cómo. Cuando logeas un error, incluye el contexto: qué operación se estaba ejecutando, con qué datos, qué configuración se estaba usando, cuántos reintentos se han hecho. Este contexto adicional puede parecer redundante cuando todo funciona bien, pero se convierte en oro puro cuando necesitas diagnosticar un problema a las 3 AM.

**Ejemplo de contexto insuficiente:**

```python
logger.error("Failed")
```

**Ejemplo con contexto rico:**

```python
logger.error(f"Failed to connect to {db_host}: {error_message}", extra={
    'db_host': db_host,
    'retry_attempt': retry_count,
    'timeout_seconds': timeout
})
```

La segunda versión te da toda la información necesaria para entender y potencialmente reproducir el problema, mientras que la primera es prácticamente inútil.

### Usa los Niveles de Log Apropiadamente

Los niveles de log no son decoración, son herramientas de comunicación. Cada nivel tiene un propósito específico y usarlos correctamente hace la diferencia entre logs útiles y ruido indescifrable.

El nivel **DEBUG** es tu amigo durante el desarrollo pero tu enemigo en producción. Está diseñado para ese detalle extremadamente granular que necesitas cuando estás construyendo una funcionalidad nueva o persiguiendo un bug esquivo. "Variable x ahora tiene el valor 42", "Entrando al método process_data", "Iterando sobre el elemento 1523 de 10000". Esta información es valiosa cuando estás desarrollando, pero en producción genera volúmenes masivos de datos que dificultan encontrar información real.

El nivel **INFO** es el caballo de batalla de producción. Aquí van los eventos normales del ciclo de vida de tu aplicación: cuando un job inicia, cuando se completan procesamiento de datos, cuando se alcanzan hitos significativos. Estos logs te permiten entender el flujo normal de operaciones sin ahogarte en detalles.

**WARNING** es para esas situaciones que no son ideales pero que tu aplicación puede manejar. Un registro con datos inválidos que se salta, un servicio externo que respondió lento pero dentro del timeout, un reintento exitoso después de un fallo temporal. Son señales de que algo no está perfecto, pero no es crítico.

**ERROR** marca operaciones que fallaron y que requieren atención. No pudo conectarse a la base de datos, falló el procesamiento de un archivo, una API externa devolvió un error. Estos logs deberían desencadenar investigación.

**CRITICAL** es para esas situaciones donde el sistema está en un estado peligroso o no funcional. La base de datos está corrupta, no hay memoria disponible, un servicio esencial está completamente caído. Estos logs deberían desencadenar alertas inmediatas a tu equipo de guardia.

### Implementa Correlación de Logs

En sistemas distribuidos o aplicaciones con múltiples componentes, un solo request del usuario puede generar docenas de operaciones a través de diferentes servicios. Sin una forma de correlacionar estos logs, es como intentar resolver un rompecabezas donde las piezas están mezcladas con las de otros diez rompecabezas diferentes.

La solución es usar identificadores únicos que viajan con cada operación a través de todo el sistema. Al inicio de un proceso, generas un Request ID o Trace ID único, y lo incluyes en cada mensaje de log relacionado con esa operación. Puede ser un UUID, un timestamp combinado con algún identificador, o cualquier esquema que garantice unicidad.

```python
import uuid

request_id = str(uuid.uuid4())

logger.info(f"[{request_id}] Starting ETL")
logger.info(f"[{request_id}] Extracted 1000 rows")
logger.error(f"[{request_id}] Failed to load data")
```

Cuando algo falla, puedes buscar ese `request_id` específico y ver el recorrido completo de esa operación: cuándo empezó, qué servicios tocó, dónde se ralentizó, y exactamente dónde falló. Es la diferencia entre buscar una aguja en un pajar y tener un mapa que te lleva directamente a ella.

### Gestiona la Retención de Logs Inteligentemente

Los logs ocupan espacio, y en sistemas de alto volumen pueden generar gigabytes o incluso terabytes de datos diariamente. No puedes guardarlos para siempre, pero tampoco quieres borrar información crítica prematuramente.

La estrategia típica es aplicar políticas de retención basadas en el nivel de severidad y la frecuencia de acceso. Los logs de DEBUG, que son extremadamente voluminosos y raramente se consultan después del desarrollo, pueden mantenerse solo por uno a tres días. Los logs de INFO, que representan el grueso de la actividad normal, suelen conservarse entre una semana y un mes, suficiente para análisis de tendencias y troubleshooting de problemas recientes.

Los logs de WARNING y ERROR tienen un valor más duradero porque documentan problemas potenciales y reales, por lo que es común mantenerlos por tres meses. Los logs CRITICAL, que documentan incidentes serios, a menudo se conservan por un año o más porque pueden ser necesarios para análisis post-mortem, auditorías, o investigaciones de seguridad.

La rotación automática de logs es esencial para evitar que un disco se llene y tumbe tu aplicación. Python proporciona mecanismos integrados para esto:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10 MB por archivo
    backupCount=5  # Mantener los últimos 5 archivos
)
```

Esto crea un sistema donde cada archivo de log puede crecer hasta 10 MB, momento en el cual se archiva y se comienza uno nuevo. Solo se mantienen los últimos 5 archivos, eliminando automáticamente los más antiguos. Es una forma simple pero efectiva de evitar que los logs consuman todo tu espacio de almacenamiento mientras mantienes un historial razonable.

---

## 7.6 Herramientas de Monitorización (Panorama)

Este módulo cubre monitorización **básica** (logs, health checks, métricas simples).

En producción real, se usan herramientas avanzadas:

| Herramienta | Para qué |
|-------------|----------|
| **Prometheus** | Colección de métricas (CPU, memoria, latencia, custom) |
| **Grafana** | Visualización de métricas (dashboards, gráficas) |
| **ELK Stack** | Elasticsearch + Logstash + Kibana (búsqueda/agregación de logs) |
| **Datadog** | Monitorización SaaS todo-en-uno |
| **Sentry** | Error tracking y alertas |
| **PagerDuty** | On-call management y alertas críticas |

---

## 7.7 Ejemplo Completo: ETL con Monitorización

```python
#!/usr/bin/env python3
"""
ETL job con logging, métricas y health checks.
"""
import logging
import json
import sys
from datetime import datetime
from collections import defaultdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Métricas
metrics = defaultdict(int)
start_time = datetime.now()

def extract_data():
    """Extrae datos."""
    logger.info("=== EXTRACT ===")
    # Simular extracción
    data = [{'id': i, 'value': i*2} for i in range(1000)]
    metrics['extracted'] = len(data)
    logger.info(f"Extracted {len(data)} records")
    return data

def transform_data(data):
    """Transforma datos."""
    logger.info("=== TRANSFORM ===")
    transformed = []
    
    for record in data:
        try:
            # Validación
            if record['value'] < 0:
                metrics['invalid'] += 1
                logger.warning(f"Invalid record: {record}")
                continue
            
            # Transformación
            record['value_squared'] = record['value'] ** 2
            transformed.append(record)
            metrics['transformed'] += 1
            
        except Exception as e:
            metrics['errors'] += 1
            logger.error(f"Error transforming record {record}: {e}")
    
    logger.info(f"Transformed {len(transformed)} records")
    return transformed

def load_data(data):
    """Carga datos."""
    logger.info("=== LOAD ===")
    # Simular carga
    metrics['loaded'] = len(data)
    logger.info(f"Loaded {len(data)} records")

def print_summary():
    """Imprime resumen con métricas."""
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info("=== SUMMARY ===")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Extracted: {metrics['extracted']}")
    logger.info(f"Transformed: {metrics['transformed']}")
    logger.info(f"Invalid: {metrics['invalid']}")
    logger.info(f"Errors: {metrics['errors']}")
    logger.info(f"Loaded: {metrics['loaded']}")
    
    success_rate = metrics['loaded'] / metrics['extracted'] * 100 if metrics['extracted'] > 0 else 0
    logger.info(f"Success rate: {success_rate:.2f}%")

if __name__ == "__main__":
    try:
        logger.info("Starting ETL job")
        
        data = extract_data()
        transformed = transform_data(data)
        load_data(transformed)
        
        print_summary()
        
        logger.info("✓ ETL job completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"✗ ETL job failed: {e}", exc_info=True)
        sys.exit(1)
```

Output:

```
2024-03-06 08:15:23 - __main__ - INFO - Starting ETL job
2024-03-06 08:15:23 - __main__ - INFO - === EXTRACT ===
2024-03-06 08:15:23 - __main__ - INFO - Extracted 1000 records
2024-03-06 08:15:23 - __main__ - INFO - === TRANSFORM ===
2024-03-06 08:15:24 - __main__ - INFO - Transformed 1000 records
2024-03-06 08:15:24 - __main__ - INFO - === LOAD ===
2024-03-06 08:15:24 - __main__ - INFO - Loaded 1000 records
2024-03-06 08:15:24 - __main__ - INFO - === SUMMARY ===
2024-03-06 08:15:24 - __main__ - INFO - Duration: 1.23 seconds
2024-03-06 08:15:24 - __main__ - INFO - Extracted: 1000
2024-03-06 08:15:24 - __main__ - INFO - Transformed: 1000
2024-03-06 08:15:24 - __main__ - INFO - Invalid: 0
2024-03-06 08:15:24 - __main__ - INFO - Errors: 0
2024-03-06 08:15:24 - __main__ - INFO - Loaded: 1000
2024-03-06 08:15:24 - __main__ - INFO - Success rate: 100.00%
2024-03-06 08:15:24 - __main__ - INFO - ✓ ETL job completed successfully
```

---

## Resumen de Conceptos Clave

1. **Logs:** Diario de tu aplicación (qué pasó, cuándo, por qué).
2. **Niveles:** DEBUG, INFO, WARNING, ERROR, CRITICAL.
3. **Logs estructurados:** JSON para parseo automático.
4. **Health checks:** Endpoint HTTP que valida si app está funcionando.
5. **Métricas:** Números clave (latencia, throughput, error rate).
6. **Alertas:** Notificar equipo si algo crítico falla.
7. **Best practices:** contexto, niveles correctos, correlación, retención.

---

## Próximo: Práctica 7.1

En la práctica, implementarás logging en una app real, crearás health checks, y configurarás alertas en pipelines Jenkins/GitLab.
