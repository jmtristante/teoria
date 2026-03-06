# Práctica 5.1: Pipeline Completa - Jenkins y GitLab

**Duración estimada:** 90 minutos  
**Requisitos previos:** Módulos 3 y 4 completados. Jenkins y GitLab corriendo.

---

## Objetivo

Construir una pipeline CI/CD completa que incluya todos los stages:
1. Checkout código
2. Instalar dependencias
3. Ejecutar tests
4. Build imagen Docker
5. Push a registry
6. Deploy (ejecutar contenedor)

Implementarla en **Jenkins**, luego replicarla en **GitLab CI**.

---

## Parte 0: Preparar Aplicación y Repositorio (15 min)

### Paso 0.1: Crear directorio base

```bash
mkdir -p ~/formacion-cd/app-pipeline && cd ~/formacion-cd/app-pipeline
```

### Paso 0.2: Crear estructura de archivos

```bash
mkdir -p tests
touch app.py tests/test_app.py Dockerfile Jenkinsfile .gitlab-ci.yml .gitignore requirements.txt
```

### Paso 0.3: Crear app.py

```python
#!/usr/bin/env python3
"""
Aplicación de procesamiento de datos.
Pipeline completa: deploy en dev/test/prod.
"""
import os
import sys

def get_environment():
    """Retorna entorno actual."""
    return os.getenv("APP_ENV", "development")

def transform_text(text):
    """Transforma texto a mayúscula."""
    return text.upper()

if __name__ == "__main__":
    env = get_environment()
    print(f"✓ App running in: {env}")
    
    # Demo
    result = transform_text("hello pipeline")
    print(f"✓ Transform result: {result}")
    sys.exit(0)
```

### Paso 0.4: Crear tests

**tests/test_app.py:**

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import transform_text, get_environment

def test_transform_text():
    """Test transformación."""
    result = transform_text("test")
    assert result == "TEST"

def test_get_environment():
    """Test lectura de env."""
    os.environ["APP_ENV"] = "test"
    env = get_environment()
    assert env == "test"
```

### Paso 0.5: Crear requirements.txt

```
pytest==7.4.3
```

### Paso 0.6: Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY tests/ tests/

ENV APP_ENV=development

CMD ["python", "app.py"]
```

### Paso 0.7: Crear .gitignore

```
__pycache__/
*.pyc
.pytest_cache/
venv/
```

### Paso 0.8: Inicializar Git

```bash
cd ~/formacion-cd/app-pipeline
git init
git add .
git commit -m "Initial commit: pipeline app"
```

### ✓ Checkpoint 0: App y repo listos

---

## PARTE 1: PIPELINE EN JENKINS (40 min)

### Paso 1.1: Crear Jenkinsfile

**Jenkinsfile:**

```groovy
pipeline {
    agent any
    
    environment {
        REGISTRY = "localhost:5000"
        APP_NAME = "app-pipeline"
        BUILD_VERSION = "${BUILD_NUMBER}"
    }
    
    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['dev', 'test', 'prod'],
            description: 'Environment to deploy'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "=== Stage 1: Checkout ==="
                sh '''
                    pwd
                    ls -la
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo "=== Stage 2: Install Dependencies ==="
                sh '''
                    set -e
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    echo "✓ Dependencies installed"
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo "=== Stage 3: Test ==="
                sh '''
                    set -e
                    . venv/bin/activate
                    python -m pytest tests/ -v
                    echo "✓ Tests passed"
                '''
            }
        }
        
        stage('Build Docker') {
            steps {
                echo "=== Stage 4: Build Docker Image ==="
                sh '''
                    set -e
                    IMAGE="${REGISTRY}/${APP_NAME}:${BUILD_NUMBER}"
                    echo "Building: $IMAGE"
                    docker build -t ${IMAGE} -t ${REGISTRY}/${APP_NAME}:latest .
                    docker images | grep ${APP_NAME}
                    echo "✓ Docker image built"
                '''
            }
        }
        
        stage('Push Registry') {
            steps {
                echo "=== Stage 5: Push to Registry ==="
                sh '''
                    set -e
                    IMAGE="${REGISTRY}/${APP_NAME}:${BUILD_NUMBER}"
                    echo "Pushing: $IMAGE"
                    # Nota: en casa, docker push requiere registry running
                    # docker push ${IMAGE}
                    echo "✓ (Skipped in demo, would push to registry)"
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo "=== Stage 6: Deploy (Env=${DEPLOY_ENV}) ==="
                sh '''
                    set -e
                    IMAGE="${REGISTRY}/${APP_NAME}:${BUILD_NUMBER}"
                    CONTAINER="${APP_NAME}-${DEPLOY_ENV}"
                    
                    echo "Stopping old container..."
                    docker stop ${CONTAINER} || true
                    docker rm ${CONTAINER} || true
                    
                    echo "Starting new container..."
                    docker run -d \\
                        --name ${CONTAINER} \\
                        -e APP_ENV=${DEPLOY_ENV} \\
                        ${IMAGE}
                    
                    sleep 2
                    docker logs ${CONTAINER}
                    echo "✓ Deployed to ${DEPLOY_ENV}"
                '''
            }
        }
    }
    
    post {
        always {
            echo "=== Pipeline finished ==="
            sh 'rm -rf venv'
        }
        success {
            echo "✓ Pipeline succeeded"
        }
        failure {
            echo "✗ Pipeline failed"
        }
    }
}
```

### Paso 1.2: Commit Jenkinsfile

```bash
cd ~/formacion-cd/app-pipeline
git add Jenkinsfile
git commit -m "Add Jenkinsfile with 6 stages"
```

### Paso 1.3: Crear Pipeline Job en Jenkins

1. Jenkins URL: `http://localhost:8080`
2. "New Item" → Name: `app-pipeline-jenkins`
3. Type: **Pipeline**
4. Click OK

### Paso 1.4: Configurar Pipeline Definition

En la sección "Pipeline":

- **Definition:** "Pipeline script"
- **Script:** Copiar contenido de Jenkinsfile manualmente, O usar "Lightweight checkout" si repos Git accesible

(Para demo, pegamos Jenkinsfile directamente en UI.)

### Paso 1.5: Agregar parámetro DEPLOY_ENV

En "General", marcar "This project is parameterized":

- Type: Choice
- Name: `DEPLOY_ENV`
- Choices: `dev test prod`

### Paso 1.6: Guardar

Click "Save".

### Paso 1.7: Ejecutar Build en Jenkins

1. "Build with Parameters"
2. Select `DEPLOY_ENV = dev`
3. Click "Build"

### Paso 1.8: Ver logs

En "Console Output", debería ver todas las 6 etapas ejecutándose.

### Paso 1.9: Validar contenedor corriendo

```bash
docker ps | grep app-pipeline-dev
docker logs app-pipeline-dev
```

Debería ver: `✓ App running in: dev` e `✓ Transform result: HELLO PIPELINE`

### ✓ Checkpoint 1: Pipeline en Jenkins exitosa

---

## PARTE 2: MISMA PIPELINE EN GITLAB CI (35 min)

### Paso 2.1: Crear GitLab Repo

1. GitLab: `http://localhost:81` (o URL correcta)
2. "New project" → Name: `app-pipeline-gitlab`
3. Visibility: Public
4. Click "Create"

### Paso 2.2: Clone y llenar repo

```bash
cd ~/formacion-cd
git clone http://localhost:81/root/app-pipeline-gitlab.git
cd app-pipeline-gitlab

# Copiar archivos desde directory anterior
cp ~/formacion-cd/app-pipeline/* .

# Excluir Jenkinsfile
rm -f Jenkinsfile
```

### Paso 2.3: Crear .gitlab-ci.yml

```yaml
stages:
  - checkout
  - install
  - test
  - build
  - push
  - deploy

variables:
  REGISTRY: "localhost:5000"
  APP_NAME: "app-pipeline"

stage_checkout:
  stage: checkout
  script:
    - echo "=== Stage 1: Checkout ==="
    - pwd && ls -la
  artifacts:
    paths:
      - app.py
      - tests/
      - requirements.txt
    expire_in: 1 hour

stage_install:
  stage: install
  image: python:3.11
  script:
    - echo "=== Stage 2: Install Dependencies ==="
    - pip install -r requirements.txt
    - echo "✓ Dependencies installed"
  artifacts:
    paths:
      - requirements.txt
    expire_in: 1 hour

stage_test:
  stage: test
  image: python:3.11
  script:
    - echo "=== Stage 3: Test ==="
    - pip install -r requirements.txt
    - python -m pytest tests/ -v
    - echo "✓ Tests passed"

stage_build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Stage 4: Build Docker Image ==="
    - export IMAGE="${REGISTRY}/${APP_NAME}:${CI_PIPELINE_ID}"
    - echo "Building: $IMAGE"
    - docker build -t ${IMAGE} -t ${REGISTRY}/${APP_NAME}:latest .
    - docker images | grep ${APP_NAME}
    - echo "✓ Docker image built"

stage_push:
  stage: push
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Stage 5: Push to Registry ==="
    - export IMAGE="${REGISTRY}/${APP_NAME}:${CI_PIPELINE_ID}"
    - echo "Would push: $IMAGE"
    - echo "✓ (Skipped in demo)"
  when: manual

stage_deploy:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo "=== Stage 6: Deploy (Dev) ==="
    - export IMAGE="${REGISTRY}/${APP_NAME}:${CI_PIPELINE_ID}"
    - export CONTAINER="app-pipeline-dev"
    - docker stop ${CONTAINER} || true
    - docker rm ${CONTAINER} || true
    - docker run -d --name ${CONTAINER} -e APP_ENV=dev ${IMAGE}
    - sleep 2
    - docker logs ${CONTAINER}
    - echo "✓ Deployed to dev"
  when: manual
  environment:
    name: development
```

### Paso 2.4: Commit y push

```bash
cd ~/formacion-cd/app-pipeline-gitlab
git add .
git commit -m "Add .gitlab-ci.yml pipeline"
git push origin main
```

Si pide credenciales:

```bash
git config user.email "student@training"
git config user.name "Student"
```

### Paso 2.5: Verificar pipeline en GitLab UI

Proyecto → "CI/CD" → "Pipelines"

Debería haber un pipeline. Click para ver detalles.

### Paso 2.6: Ejecutar stages

Click en cada stage "play" (manual) para ejecutar.

Orden recomendado:
1. stage_checkout
2. stage_install
3. stage_test
4. stage_build
5. stage_push (manual)
6. stage_deploy (manual)

### Paso 2.7: Validar logs

Al hacer cada stage, ver logs en UI.

### Paso 2.8: Validar contenedor

```bash
docker ps | grep app-pipeline-dev
docker logs app-pipeline-dev
```

### ✓ Checkpoint 2: Pipeline en GitLab exitosa

---

## PARTE 3: Comparación y Entendimiento (10 min)

### Tabla Comparativa

| Aspecto | Jenkins | GitLab CI |
|---------|---------|-----------|
| Definición de pipeline | Jenkinsfile (Groovy) | .gitlab-ci.yml (YAML) |
| Trigger | Manual o webhook Git | Automático o manual |
| Stages | Declarados explícitos | Stages + dependencias |
| Variables | `${VAR}` (Groovy) | `$VAR` (YAML) |
| Artifacts | `archiveArtifacts` | `artifacts:` |
| Logs | Console Output en Jenkins | Logs en GitLab UI |
| Deploy manual | `input` o `when: manual` | `when: manual` |
| Secrets | Jenkins Credentials | GitLab Protected Variables |

### Conceptos Clave Aprendidos

1. **6 Stages universales:**
   - Checkout: recupera código
   - Install: dependencias
   - Test: validación
   - Build: artefacto (Docker image)
   - Push: distribución a registry
   - Deploy: ejecución en producción

2. **Parametrización:**
   - Jenkins: `choice` parámetro
   - GitLab: variables de proyecto o inline

3. **Environments:** Jenkins y GitLab rastrean dónde se desplegó.

4. **Manual triggers:**
   - Jenkins: parámetros en build
   - GitLab: `when: manual`

---

## Troubleshooting

### ❌ Error: "Docker image not found"

**Solución:** Asegurar que Docker está corriendo y accesible en pipeline.

```bash
docker ps  # Verificar Docker
```

### ❌ Error: "Pipeline stuck pending"

**Solución:** GitLab necesita runner registrado y conectado.

```bash
# Verificar runner
curl http://localhost:81/api/v4/runners  # En GitLab
```

### ❌ Error: "Python module not found"

**Solución:** Instalar pytest antes de ejecutar tests.

```bash
pip install -r requirements.txt
```

---

## Validación Final

**Checklist:**

- [ ] Aplicación Python creada y testeada localmente
- [ ] Jenkinsfile definido con 6 stages
- [ ] Pipeline Jenkins creada y ejecutada
- [ ] Contenedor corriendo en dev (Jenkins)
- [ ] .gitlab-ci.yml definido con 6 stages
- [ ] Pipeline GitLab creada y ejecutada
- [ ] Contenedor corriendo en dev (GitLab)
- [ ] Entiendes diferencia sintaxis Groovy vs YAML
- [ ] Reconoces patrón universal de 6 stages en ambas herramientas

---

## Resumen

Acabas de construir la **misma pipeline en dos tecnologías distintas**.

**Jenkins** usa Groovy (imperativo), **GitLab CI** usa YAML (declarativo).

Pero el concepto es idéntico: **Checkout → Install → Test → Build → Push → Deploy**.

Esto es lo que importa: el flujo de procedimiento, no la sintaxis específica.
