# Práctica 5.2: Gestión de Configuración - Jenkins y GitLab

**Duración estimada:** 45-60 minutos  
**Requisitos previos:** Práctica 5.1 completada.

---

## Objetivo

Entender y practicar cómo gestionar configuración diferente según entornos (dev, test, prod) en pipelines CI/CD, usando:

1. Archivos `.env` en aplicación.
2. Variables de entorno en Jenkins.
3. Variables Protected en GitLab.
4. Cambio de comportamiento según entorno.

---

## Conceptos Base (5 min)

### Problema: Hardcoding vs. Configuración

❌ **Incorrecto (hardcoded):**

```python
DB_HOST = "prod-db.internal"  # ← Fijo, problemático
```

✅ **Correcto (variable):**

```python
DB_HOST = os.getenv("DB_HOST", "localhost")  # ← Flexible
```

Con variables, misma imagen Docker corre en:
- **dev:** `DB_HOST=localhost`
- **test:** `DB_HOST=test-db`
- **prod:** `DB_HOST=prod-db.internal`

---

## PARTE 1: Actualizar app.py con Configuración (10 min)

### Paso 1.1: Crear app mejorada

Editar `app.py` (desde practica-5.1):

```python
#!/usr/bin/env python3
"""
Aplicación con configuración por entorno.
"""
import os
from dotenv import load_dotenv  # Opcional si lo instalas

# Cargar .env si existe
load_dotenv(verbose=True)

class Config:
    """Configuración centralizada."""
    
    APP_ENV = os.getenv("APP_ENV", "development")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    REPLICAS = int(os.getenv("REPLICAS", "1"))
    
    @classmethod
    def print_config(cls):
        """Debug: mostrar configración actual."""
        return {
            "environment": cls.APP_ENV,
            "db_host": cls.DB_HOST,
            "db_port": cls.DB_PORT,
            "log_level": cls.LOG_LEVEL,
            "replicas": cls.REPLICAS,
        }

def transform_text(text):
    """Transforma texto."""
    return text.upper()

if __name__ == "__main__":
    import json
    
    print("=== Application Starting ===")
    config = Config.print_config()
    print(json.dumps(config, indent=2))
    
    result = transform_text("config management")
    print(f"\nTransform: {result}")
    
    print("\n✓ App executed successfully")
```

### Paso 1.2: Actualizar requirements.txt

```
pytest==7.4.3
python-dotenv==1.0.0
```

### Paso 1.3: Crear .env.example (documentación)

**.env.example:**

```
# Ejemplo de variables de entorno requeridas

APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
LOG_LEVEL=DEBUG
REPLICAS=1
```

### Paso 1.4: Actualizar .gitignore

```
__pycache__/
*.pyc
.pytest_cache/
venv/
.env              # ← Agregar local .env
.env.local
```

### Paso 1.5: Test local

```bash
cd ~/formacion-cd/app-pipeline

# Crear .env local (no se commitea)
cat > .env << 'EOF'
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
LOG_LEVEL=DEBUG
REPLICAS=1
EOF

# Test
python app.py
```

Deberías ver:

```
=== Application Starting ===
{
  "environment": "development",
  "db_host": "localhost",
  "db_port": "5432",
  "log_level": "DEBUG",
  "replicas": 1
}

Transform: CONFIG MANAGEMENT

✓ App executed successfully
```

---

## PARTE 2: Configuración en JENKINS (15 min)

### Paso 2.1: Crear Global Properties en Jenkins

1. "Manage Jenkins" → "Configure System"
2. Buscar sección "Global properties"
3. Marcar checkbox "Environment variables"
4. Click "Add":

| Variable | Value |
|----------|-------|
| `DEFAULT_DB_HOST` | `localhost` |
| `DEFAULT_LOG_LEVEL` | `DEBUG` |

5. Click "Save"

### Paso 2.2: Actualizar Jenkinsfile con variables

Editar o crear nuevo Jenkinsfile:

```groovy
pipeline {
    agent any
    
    environment {
        APP_NAME = "app-config"
        REGISTRY = "localhost:5000"
    }
    
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['dev', 'test', 'prod'],
            description: 'Environment'
        )
    }
    
    stages {
        stage('Setup Config') {
            steps {
                echo "=== Setting up configuration for ${DEPLOY_ENV} ==="
                script {
                    // Variables por entorno
                    if (params.DEPLOY_ENV == 'dev') {
                        env.DB_HOST = 'localhost'
                        env.LOG_LEVEL = 'DEBUG'
                        env.REPLICAS = '1'
                    } else if (params.DEPLOY_ENV == 'test') {
                        env.DB_HOST = 'test-db'
                        env.LOG_LEVEL = 'INFO'
                        env.REPLICAS = '2'
                    } else if (params.DEPLOY_ENV == 'prod') {
                        env.DB_HOST = 'prod-db.internal'
                        env.LOG_LEVEL = 'ERROR'
                        env.REPLICAS = '3'
                    }
                }
                echo "✓ Config: DB_HOST=${DB_HOST}, LOG_LEVEL=${LOG_LEVEL}, REPLICAS=${REPLICAS}"
            }
        }
        
        stage('Build & Test') {
            steps {
                echo "=== Building ==="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m pytest tests/ -v
                '''
            }
        }
        
        stage('Build Docker') {
            steps {
                echo "=== Building Docker with config ==="
                sh '''
                    IMAGE="localhost:5000/app-config:${BUILD_NUMBER}"
                    docker build -t ${IMAGE} .
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo "=== Deploying to ${DEPLOY_ENV} ==="
                sh '''
                    IMAGE="localhost:5000/app-config:${BUILD_NUMBER}"
                    CONTAINER="app-config-${DEPLOY_ENV}"
                    
                    docker stop ${CONTAINER} || true
                    docker rm ${CONTAINER} || true
                    
                    echo "Starting with: DB_HOST=${DB_HOST}, LOG_LEVEL=${LOG_LEVEL}"
                    docker run -d \\
                        --name ${CONTAINER} \\
                        -e APP_ENV=${DEPLOY_ENV} \\
                        -e DB_HOST=${DB_HOST} \\
                        -e LOG_LEVEL=${LOG_LEVEL} \\
                        -e REPLICAS=${REPLICAS} \\
                        ${IMAGE}
                    
                    sleep 2
                    docker logs ${CONTAINER}
                '''
            }
        }
    }
    
    post {
        always {
            sh 'rm -rf venv'
        }
    }
}
```

### Paso 2.3: Crear Pipeline Job

1. Jenkins: "New Item" → Name: `app-config`
2. Type: "Pipeline"
3. En "Pipeline" → "Definition": "Pipeline script"
4. Pegar Jenkinsfile anterior
5. Add parameter: Choice `DEPLOY_ENV` con opciones dev/test/prod
6. Click "Save"

### Paso 2.4: Build con parámetro

1. "Build with Parameters"
2. Select `DEPLOY_ENV = prod`
3. Click "Build"
4. Ver Console Output

Debería ver:

```
=== Setting up configuration for prod ===
✓ Config: DB_HOST=prod-db.internal, LOG_LEVEL=ERROR, REPLICAS=3
```

### Paso 2.5: Validar contenedor

```bash
docker logs app-config-prod
```

Debería ver config de producción en logs.

### ✓ Checkpoint 1: Variables en Jenkins OK

---

## PARTE 3: Configuración en GITLAB (15 min)

### Paso 3.1: Crear Variables de Proyecto

1. GitLab proyecto: "Settings" → "CI/CD" → "Variables"
2. Click "Add variable" para cada entorno:

**Para dev:**
- Key: `DB_HOST_DEV`
- Value: `localhost`
- Check "Protected": NO
- Check "Masked": NO

Repetir:
- `DB_HOST_TEST = test-db`
- `DB_HOST_PROD = prod-db.internal`
- `LOG_LEVEL_DEV = DEBUG`
- `LOG_LEVEL_TEST = INFO`
- `LOG_LEVEL_PROD = ERROR`

### Paso 3.2: Crear .gitlab-ci.yml con variables

```yaml
stages:
  - setup
  - build
  - deploy

variables:
  APP_NAME: "app-config"
  REGISTRY: "localhost:5000"

# Dynamic config based on branch/tag
.env_config:
  script:
    - |
      if [ "$CI_COMMIT_BRANCH" = "develop" ]; then
        export DEPLOY_ENV=dev
        export DB_HOST=$DB_HOST_DEV
        export LOG_LEVEL=$LOG_LEVEL_DEV
      elif [ "$CI_COMMIT_BRANCH" = "main" ]; then
        export DEPLOY_ENV=test
        export DB_HOST=$DB_HOST_TEST
        export LOG_LEVEL=$LOG_LEVEL_TEST
      elif [ "$CI_COMMIT_TAG" ]; then
        export DEPLOY_ENV=prod
        export DB_HOST=$DB_HOST_PROD
        export LOG_LEVEL=$LOG_LEVEL_PROD
      fi
      echo "Environment: $DEPLOY_ENV, DB: $DB_HOST"

setup_config:
  stage: setup
  script:
    - echo "=== Setup Config ==="
    - !reference [.env_config, script]
    - echo "Config set for $DEPLOY_ENV"
  artifacts:
    reports:
      dotenv: config.env

build_app:
  stage: build
  image: python:3.11
  script:
    - echo "=== Building App ==="
    - pip install -r requirements.txt
    - python -m pytest tests/ -v
    - echo "✓ Build complete"

build_docker:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Building Docker ==="
    - export IMAGE="${REGISTRY}/${APP_NAME}:${CI_PIPELINE_ID}"
    - docker build -t ${IMAGE} .
    - docker images | grep app-config

deploy_manual:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Deploying ==="
    - export DEPLOY_ENV=${DEPLOY_ENV:-dev}
    - export DB_HOST=${DB_HOST_DEV}
    - export LOG_LEVEL=${LOG_LEVEL_DEV}
    - export IMAGE="${REGISTRY}/${APP_NAME}:${CI_PIPELINE_ID}"
    - |
      docker run -d \
        --name app-config-${DEPLOY_ENV} \
        -e APP_ENV=${DEPLOY_ENV} \
        -e DB_HOST=${DB_HOST} \
        -e LOG_LEVEL=${LOG_LEVEL} \
        ${IMAGE}
    - sleep 2
    - docker logs app-config-${DEPLOY_ENV}
  when: manual
```

### Paso 3.3: Push a GitLab

```bash
cd ~/formacion-cd/app-pipeline-gitlab

# Actualizar archivos
cp ~/formacion-cd/app-pipeline/app.py .
cp ~/formacion-cd/app-pipeline/requirements.txt .
cp ~/formacion-cd/app-pipeline/.gitignore .
cp ~/formacion-cd/app-pipeline/.env.example .

# Actualizar .gitlab-ci.yml (pegado arriba)

git add .
git commit -m "Add config management"
git push origin main
```

### Paso 3.4: Ver Pipeline en GitLab

Project → "CI/CD" → "Pipelines"

Debería haber nueva pipeline. Click para expandir stages.

### Paso 3.5: Deploy manual

Click en stage "deploy_manual" → "play"

Ver logs.

### Paso 3.6: Validar

```bash
docker logs app-config-dev
```

---

## PARTE 4: Entender jerarquía de Variables (5 min)

### Variable Precedence

En GitLab (de mayor a menor prioridad):

1. **Job-level variables**
2. **Protected variables** (rama/tag específico)
3. **Project variables**
4. **Group variables**
5. **Instance variables**

En Jenkins:

1. **Build parameters**
2. **Job-level environment variables**
3. **Global properties**
4. **Default values en código**

### Debug: Ver variables en pipeline

**Jenkins:**

```groovy
sh 'env | sort'  // Listar todas las variables
```

**GitLab:**

```yaml
script:
  - env | sort  # Listar todas las variables
```

---

## PARTE 5: Best Practices (5 min)

### ✅ DO

- ✅ Variables en CI/CD system, no en código.
- ✅ Usar `.env.example` como documentación.
- ✅ Secrets (password, tokens) con Protected en GitLab.
- ✅ Documentar qué variables se requieren.

### ❌ DON'T

- ❌ Hardcodear `DB_HOST="prod..."` en app.py.
- ❌ Commitear `.env` real (solo `.env.example`).
- ❌ Mezclar variables de dev y prod en un único archivo.

---

## Validación Final

**Checklist:**

- [ ] app.py lee variables con `os.getenv()`
- [ ] `.env.example` documenta variables necesarias
- [ ] `.gitignore` excluye `.env` local
- [ ] Jenkinsfile establece variables por entorno
- [ ] Build Jenkins con `DEPLOY_ENV=prod` inyecta variables correctas
- [ ] GitLab tiene Protected Variables creadas
- [ ] `.gitlab-ci.yml` usa esas variables
- [ ] Docker container recibe variables de entorno
- [ ] `docker logs app-config-prod` muestra `prod-db.internal`
- [ ] `docker logs app-config-dev` muestra `localhost`

---

## Concepto Final

Separar **código** de **configuración** es fundamental.

Tu aplicación es **agnóstica**: mismo código ejecuta en dev/test/prod.

Lo que cambia es la **configuración inyectada en tiempo de ejecución**.

```
Código (inmutable) +  Variables (inyectadas) = Aplicación adaptada al entorno
```

Eso es CI/CD profesional.
