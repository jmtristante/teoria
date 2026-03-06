# Práctica 7.1: Logs y Monitorización

**Duración estimada:** 60 minutos  
**Requisitos previos:** Módulos 3-6 completados. Docker, Jenkins y GitLab configurados.

---

## Objetivo

Implementar monitorización básica en una aplicación:
1. Logging estructurado en Python.
2. Ver logs de contenedores Docker.
3. Crear health check endpoint.
4. Implementar health check en pipeline CI/CD.
5. Configurar alertas por email en caso de fallo.

---

## Fase 1: Crear Aplicación con Logging (15 min)

### Paso 1.1: Preparar estructura

```bash
mkdir -p ~/formacion-cd/monitoring-app && cd ~/formacion-cd/monitoring-app
mkdir -p tests
touch app.py requirements.txt Dockerfile .gitignore
```

### Paso 1.2: Crear app.py con logging

```python
#!/usr/bin/env python3
"""
Aplicación de procesamiento con logging completo.
"""
import logging
import json
import sys
import os
import time
from datetime import datetime
from collections import defaultdict
from flask import Flask, jsonify

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
start_time = datetime.now()

# Métricas
metrics = defaultdict(int)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    
    uptime = (datetime.now() - start_time).total_seconds()
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "metrics": dict(metrics)
    }
    
    # Simular check de dependencia
    db_status = check_database()
    health_status["database"] = db_status
    
    if not db_status["connected"]:
        health_status["status"] = "unhealthy"
        logger.warning("Health check: database not connected")
        return jsonify(health_status), 503
    
    logger.info("Health check: OK")
    return jsonify(health_status), 200

def check_database():
    """Simula check de base de datos."""
    # En producción, esto sería conexión real
    db_host = os.getenv("DB_HOST", "localhost")
    
    # Simular fallo aleatorio 10% del tiempo
    import random
    is_connected = random.random() > 0.1
    
    return {
        "connected": is_connected,
        "host": db_host,
        "checked_at": datetime.utcnow().isoformat()
    }

@app.route('/metrics')
def metrics_endpoint():
    """Endpoint para exponer métricas."""
    logger.debug("Metrics requested")
    
    total = sum(metrics.values())
    
    return jsonify({
        "total_operations": total,
        "successful": metrics['successful'],
        "failed": metrics['failed'],
        "success_rate": (metrics['successful'] / total * 100) if total > 0 else 0
    })

@app.route('/process')
def process_data():
    """Endpoint que simula procesamiento de datos."""
    logger.info("=== Starting data processing ===")
    
    try:
        # Simular procesamiento
        num_records = 100
        logger.info(f"Processing {num_records} records")
        
        for i in range(num_records):
            # Simular fallo ocasional
            if i % 20 == 0 and i > 0:
                logger.warning(f"Record {i} has invalid data, skipping")
                metrics['failed'] += 1
                continue
            
            # Procesamiento exitoso
            metrics['successful'] += 1
            
            if i % 25 == 0:
                logger.debug(f"Processed {i}/{num_records} records")
        
        duration = 2.5  # Simular duración
        logger.info(f"Processing completed: {metrics['successful']} successful, {metrics['failed']} failed")
        logger.info(f"Duration: {duration}s")
        
        return jsonify({
            "status": "completed",
            "records_processed": metrics['successful'],
            "records_failed": metrics['failed'],
            "duration_seconds": duration
        }), 200
        
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        metrics['failed'] += 1
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    """Root endpoint."""
    logger.debug("Index page requested")
    return jsonify({
        "name": "Monitoring App",
        "version": "1.0.0",
        "endpoints": ["/health", "/metrics", "/process"]
    })

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Starting Monitoring App")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"DB Host: {os.getenv('DB_HOST', 'localhost')}")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Paso 1.3: Crear requirements.txt

```
flask==3.0.0
```

### Paso 1.4: Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV APP_ENV=production
ENV DB_HOST=localhost

EXPOSE 5000

# Health check cada 30 segundos
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
```

### Paso 1.5: Test local

```bash
cd ~/formacion-cd/monitoring-app

# Test sin Docker
pip install flask --user
python app.py
```

En otra terminal:

```bash
# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/process
curl http://localhost:5000/metrics
```

Ctrl+C para parar.

### ✓ Checkpoint 1: App con logging funciona localmente

---

## Fase 2: Ver Logs en Docker (10 min)

### Paso 2.1: Build imagen

```bash
cd ~/formacion-cd/monitoring-app
docker build -t monitoring-app:latest .
```

### Paso 2.2: Ejecutar contenedor

```bash
docker run -d \
  --name monitoring-app \
  -p 5000:5000 \
  -e APP_ENV=production \
  -e DB_HOST=prod-db.internal \
  monitoring-app:latest
```

### Paso 2.3: Ver logs en tiempo real

```bash
docker logs -f monitoring-app
```

Deberías ver:

```
2024-03-06 08:15:23 - __main__ - INFO - ==================================================
2024-03-06 08:15:23 - __main__ - INFO - Starting Monitoring App
2024-03-06 08:15:23 - __main__ - INFO - Environment: production
2024-03-06 08:15:23 - __main__ - INFO - DB Host: prod-db.internal
2024-03-06 08:15:23 - __main__ - INFO - ==================================================
```

### Paso 2.4: Generar logs con requests

En otra terminal:

```bash
# Trigger procesamiento
curl http://localhost:5000/process

# Ver health check
curl http://localhost:5000/health

# Ver métricas
curl http://localhost:5000/metrics
```

En terminal de logs, verás:

```
2024-03-06 08:16:15 - __main__ - INFO - === Starting data processing ===
2024-03-06 08:16:15 - __main__ - INFO - Processing 100 records
2024-03-06 08:16:15 - __main__ - WARNING - Record 20 has invalid data, skipping
2024-03-06 08:16:15 - __main__ - INFO - Processing completed: 95 successful, 5 failed
2024-03-06 08:16:15 - __main__ - INFO - Duration: 2.5s
2024-03-06 08:16:20 - __main__ - INFO - Health check requested
2024-03-06 08:16:20 - __main__ - INFO - Health check: OK
```

### Paso 2.5: Ver últimas 50 líneas

```bash
docker logs --tail 50 monitoring-app
```

### Paso 2.6: Filtrar logs por nivel

```bash
# Solo errores y warnings
docker logs monitoring-app 2>&1 | grep -E "WARNING|ERROR"

# Solo INFO
docker logs monitoring-app 2>&1 | grep "INFO"
```

### ✓ Checkpoint 2: Logs visibles en Docker

---

## Fase 3: Health Check en Acción (10 min)

### Paso 3.1: Ver health check automático de Docker

```bash
docker ps

# Columna STATUS debería mostrar: Up X seconds (healthy)
```

Espera 30 segundos, verifica de nuevo:

```bash
docker ps
# Si app está ok: (healthy)
# Si falla 3 veces: (unhealthy)
```

### Paso 3.2: Simular fallo de health check

Modificar app.py temporalmente para forzar fallo:

```python
@app.route('/health')
def health_check():
    # Forzar fallo
    return jsonify({"status": "unhealthy"}), 503
```

Rebuild y ejecutar:

```bash
docker stop monitoring-app && docker rm monitoring-app
docker build -t monitoring-app:latest .
docker run -d --name monitoring-app -p 5000:5000 monitoring-app:latest
```

Espera 2 minutos, luego:

```bash
docker ps
# STATUS mostrará: Up X seconds (unhealthy)
```

Ver logs de health checks:

```bash
docker logs monitoring-app | grep health
```

### Paso 3.3: Restaurar app.py

Revertir cambio en app.py (quitar forzar fallo).

Rebuild:

```bash
docker stop monitoring-app && docker rm monitoring-app
docker build -t monitoring-app:latest .
docker run -d --name monitoring-app -p 5000:5000 monitoring-app:latest
```

### ✓ Checkpoint 3: Health check funciona

---

## Fase 4: Health Check en Pipeline Jenkins (15 min)

### Paso 4.1: Crear Jenkinsfile

**Jenkinsfile:**

```groovy
pipeline {
    agent any
    
    environment {
        APP_NAME = "monitoring-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Build') {
            steps {
                echo "=== Building Docker image ==="
                sh '''
                    docker build -t ${APP_NAME}:${IMAGE_TAG} .
                    docker tag ${APP_NAME}:${IMAGE_TAG} ${APP_NAME}:latest
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo "=== Running tests ==="
                sh '''
                    echo "Tests would run here"
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo "=== Deploying application ==="
                sh '''
                    # Stop old container
                    docker stop ${APP_NAME} || true
                    docker rm ${APP_NAME} || true
                    
                    # Start new container
                    docker run -d \\
                        --name ${APP_NAME} \\
                        -p 5000:5000 \\
                        -e APP_ENV=production \\
                        ${APP_NAME}:${IMAGE_TAG}
                    
                    echo "✓ Container started"
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                echo "=== Checking application health ==="
                sh '''
                    # Wait for app to start
                    echo "Waiting for app to start..."
                    sleep 10
                    
                    # Check health endpoint
                    MAX_RETRIES=5
                    RETRY_COUNT=0
                    
                    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
                        
                        if [ "$HTTP_CODE" -eq 200 ]; then
                            echo "✓ Health check passed (HTTP $HTTP_CODE)"
                            exit 0
                        else
                            RETRY_COUNT=$((RETRY_COUNT+1))
                            echo "⚠ Health check failed (HTTP $HTTP_CODE), retry $RETRY_COUNT/$MAX_RETRIES"
                            sleep 5
                        fi
                    done
                    
                    echo "✗ Health check failed after $MAX_RETRIES retries"
                    docker logs ${APP_NAME}
                    exit 1
                '''
            }
        }
        
        stage('Verify Logs') {
            steps {
                echo "=== Verifying application logs ==="
                sh '''
                    echo "Last 20 lines of logs:"
                    docker logs --tail 20 ${APP_NAME}
                    
                    # Check for errors
                    ERROR_COUNT=$(docker logs ${APP_NAME} | grep -c "ERROR" || true)
                    
                    if [ $ERROR_COUNT -gt 0 ]; then
                        echo "⚠ Found $ERROR_COUNT errors in logs"
                    else
                        echo "✓ No errors in logs"
                    fi
                '''
            }
        }
    }
    
    post {
        always {
            echo "=== Pipeline finished ==="
        }
        success {
            echo "✓ Build successful - application is healthy"
        }
        failure {
            echo "✗ Build failed - check logs"
            sh 'docker logs ${APP_NAME} || true'
        }
    }
}
```

### Paso 4.2: Crear Pipeline Job en Jenkins

1. Jenkins: "New Item"
2. Name: `monitoring-app-cicd`
3. Type: **Pipeline**
4. "Pipeline" → "Definition": **Pipeline script**
5. Pegar Jenkinsfile
6. Click "Save"

### Paso 4.3: Ejecutar Build

"Build Now"

Ver Console Output. Deberías ver:

```
=== Checking application health ===
Waiting for app to start...
✓ Health check passed (HTTP 200)

=== Verifying application logs ===
Last 20 lines of logs:
2024-03-06 08:15:23 - __main__ - INFO - Starting Monitoring App
...
✓ No errors in logs
```

### ✓ Checkpoint 4: Health check en pipeline funciona

---

## Fase 5: Alertas por Email en Pipeline GitLab (10 min)

### Paso 5.1: Crear repo en GitLab

1. GitLab: "New project"
2. Name: `monitoring-app`
3. Visibility: Public

### Paso 5.2: Crear .gitlab-ci.yml

```yaml
stages:
  - build
  - test
  - deploy
  - health_check
  - notify

variables:
  APP_NAME: "monitoring-app"

build_image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Building Docker image ==="
    - docker build -t ${APP_NAME}:${CI_PIPELINE_ID} .
    - docker tag ${APP_NAME}:${CI_PIPELINE_ID} ${APP_NAME}:latest

test_app:
  stage: test
  image: python:3.11
  script:
    - echo "=== Running tests ==="
    - pip install flask
    - python -c "import app; print('Syntax OK')"

deploy_app:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Deploying application ==="
    - docker stop ${APP_NAME} || true
    - docker rm ${APP_NAME} || true
    - docker run -d --name ${APP_NAME} -p 5000:5000 ${APP_NAME}:${CI_PIPELINE_ID}
    - echo "✓ Container started"
  environment:
    name: production

health_check:
  stage: health_check
  image: curlimages/curl:latest
  script:
    - echo "=== Checking health ==="
    - sleep 10
    - |
      for i in 1 2 3 4 5; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
          echo "✓ Health check passed"
          exit 0
        fi
        echo "⚠ Retry $i/5"
        sleep 5
      done
      echo "✗ Health check failed"
      exit 1

notify_success:
  stage: notify
  script:
    - echo "=== Sending success notification ==="
    - |
      echo "Pipeline successful" | mail -s "Success: ${CI_PROJECT_NAME}" team@example.com || echo "Email not configured"
  when: on_success
  only:
    - main

notify_failure:
  stage: notify
  script:
    - echo "=== Sending failure notification ==="
    - |
      curl -X POST https://hooks.slack.com/services/YOUR_WEBHOOK \
        -H 'Content-Type: application/json' \
        -d '{
          "text": "❌ Pipeline failed: '"$CI_PROJECT_NAME"' - '"$CI_PIPELINE_URL"'"
        }' || echo "Slack not configured"
  when: on_failure
  only:
    - main
```

### Paso 5.3: Commit y push

```bash
cd ~/formacion-cd/monitoring-app
git init
git remote add origin http://localhost:81/root/monitoring-app.git
git add .
git commit -m "Add monitoring app with CI/CD"
git push -u origin main
```

### Paso 5.4: Ver pipeline

GitLab → Proyecto → CI/CD → Pipelines

Debería haber 5 stages ejecutándose.

### ✓ Checkpoint 5: Pipeline completa con notificaciones

---

## Fase 6: Simular Fallo y Ver Alertas (10 min)

### Paso 6.1: Introducir bug intencional

Modificar `app.py`:

```python
@app.route('/health')
def health_check():
    # Bug intencional
    raise Exception("Simulated error")
```

### Paso 6.2: Commit y push

```bash
git add app.py
git commit -m "Introduce bug in health check"
git push
```

### Paso 6.3: Ver pipeline fallar

GitLab → CI/CD → Pipelines

Stage `health_check` debería fallar.

Stage `notify_failure` debería ejecutarse.

### Paso 6.4: Ver logs del fallo

Click en `health_check` → Ver logs:

```
⚠ Retry 1/5
⚠ Retry 2/5
⚠ Retry 3/5
⚠ Retry 4/5
⚠ Retry 5/5
✗ Health check failed
```

### Paso 6.5: Revertir bug

```bash
git revert HEAD
git push
```

Pipeline debería pasar de nuevo.

---

## Troubleshooting

### ❌ Error: "curl: command not found"

**Solución:** Instalar curl en container:

```dockerfile
RUN apt-get update && apt-get install -y curl
```

### ❌ Error: "Health check timeout"

**Solución:** App puede tardar en iniciar. Aumentar sleep:

```bash
sleep 15  # En lugar de 10
```

### ❌ Error: "Email not sent"

**Solución:** Email requiere configuración SMTP. En demo, simplemente logear:

```bash
echo "Would send email to team@example.com"
```

---

## Validación Final

**Checklist:**

- [ ] app.py tiene logging estructurado (INFO, WARNING, ERROR)
- [ ] Endpoint `/health` responde 200 si healthy, 503 si unhealthy
- [ ] Endpoint `/metrics` expone contadores
- [ ] Dockerfile tiene HEALTHCHECK
- [ ] `docker logs` muestra logs de aplicación
- [ ] `docker ps` muestra (healthy) después de 30 segundos
- [ ] Jenkinsfile tiene stage Health Check con retries
- [ ] Pipeline Jenkins valida health antes de considerar deploy exitoso
- [ ] .gitlab-ci.yml tiene stage health_check
- [ ] .gitlab-ci.yml tiene notify_failure que se ejecuta cuando falla
- [ ] Simulación de fallo causa que pipeline falle y notifique

---

## Conceptos Clave Aprendidos

1. **Logging estructurado:** Usar niveles (INFO, WARNING, ERROR) y contexto.
2. **Docker logs:** Todo a stdout, Docker centraliza automáticamente.
3. **Health checks:** Endpoint HTTP que valida estado de app + dependencias.
4. **Pipeline validation:** No dar deploy por OK hasta validar health.
5. **Retries:** Reintentar health check varias veces antes de fallar.
6. **Alertas:** Notificar equipo automáticamente cuando algo falla.

---

## Extensiones Opcionales

1. **Logs estructurados JSON:** Modificar formatter para output JSON puro.
2. **Métricas de performance:** Agregar timer a cada operación.
3. **Persistent metrics:** Guardar métricas en base de datos PostgreSQL.
4. **Alertas a Slack:** Configurar webhook real de Slack.
5. **Dashboard:** Crear página `/dashboard` con métricas en tiempo real.
