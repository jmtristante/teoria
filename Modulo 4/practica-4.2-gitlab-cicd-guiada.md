# Práctica 4.2 (Guiada) — GitLab CI/CD: Pipeline Básica Declarativa

## 1) Contexto de la práctica

En esta práctica trabajarás con GitLab CI/CD. Crearás un repositorio, definirás una pipeline en `.gitlab-ci.yml` con stages de build y test, y ejecutarás jobs usando GitLab Runner local.

- **Duración estimada:** 75–90 minutos
- **Nivel:** Inicial
- **Requisitos:** cuenta en GitLab.com o acceso a GitLab local, Docker Desktop

---

## 2) Objetivos de aprendizaje

Al finalizar deberías poder:

1. Crear repositorio en GitLab.
2. Escribir `.gitlab-ci.yml` básico con stages y jobs.
3. Instalar GitLab Runner localmente.
4. Ejecutar pipeline y leer logs de jobs.
5. Entender diferencia entre stages y jobs.

---

## 3) Requisitos previos

1. Cuenta activa en GitLab.com (o GitLab local).
2. Docker instalado y en ejecución.
3. Git instalado en máquina local (`git --version`).
4. Terminal bash/sh (en máquina virtual Linux).

---

## 4) Paso a paso

### Paso 0 — Crear repositorio en GitLab

1. Ve a GitLab.com (o tu instancia local).
2. Clic en "Nuevo proyecto".
3. Elige "Crear proyecto en blanco".
4. **Nombre del proyecto:** `ci-cd-demo-python`
5. **Slug:** se genera automático.
6. **Visibilidad:** público (para simplificar).
7. Clic "Crear proyecto".

---

### Paso 1 — Clonar repositorio localmente

```bash
git clone https://gitlab.com/TU_USUARIO/ci-cd-demo-python.git
cd ci-cd-demo-python
```

Reemplaza `TU_USUARIO` con tu nombre de usuario en GitLab.

---

### Paso 2 — Crear estructura base del proyecto

Crea los siguientes archivos en la carpeta:

**Archivo: `requirements.txt`**

```
pytest==7.4.3
```

**Archivo: `app.py`**

```python
def suma(a, b):
    return a + b

def resta(a, b):
    return a - b

if __name__ == "__main__":
    print(f"Suma de 5 + 3 = {suma(5, 3)}")
    print(f"Resta de 5 - 3 = {resta(5, 3)}")
```

**Archivo: `test_app.py`**

```python
import pytest
from app import suma, resta

def test_suma():
    assert suma(5, 3) == 8
    assert suma(-1, 1) == 0

def test_resta():
    assert resta(5, 3) == 2
    assert resta(0, 5) == -5
```

**Archivo: `README.md`**

```markdown
# CI/CD Demo con GitLab

Pipeline básica para demostración de GitLab CI/CD.

## Etapas:
- Build: preparación del entorno
- Test: ejecución de tests con pytest
```

---

### Paso 3 — Crear `.gitlab-ci.yml`

Archivo crucial: **`.gitlab-ci.yml`**

```yaml
stages:
  - build
  - test
  - report

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

build_job:
  stage: build
  image: python:3.11
  script:
    - echo "========== BUILD STAGE =========="
    - python --version
    - pip install --upgrade pip
    - pip install -r requirements.txt
    - echo "Dependencias instaladas correctamente"
  artifacts:
    paths:
      - venv/
    expire_in: 1 day

test_job:
  stage: test
  image: python:3.11
  dependencies:
    - build_job
  script:
    - echo "========== TEST STAGE =========="
    - pip install -r requirements.txt
    - python -m pytest test_app.py -v
    - echo "Tests completados"
  artifacts:
    reports:
      junit: test-results.xml
    expire_in: 7 days

report_job:
  stage: report
  image: python:3.11
  script:
    - echo "========== REPORT STAGE =========="
    - echo "Pipeline completada exitosamente"
    - date
    - echo "Proyecto: ci-cd-demo-python"
  only:
    - main
    - master
```

**Explicación:**

- `stages`: define orden de ejecución.
- `image`: contenedor Docker para cada job.
- `script`: comandos a ejecutar.
- `artifacts`: archivos a guardar entre jobs.
- `dependencies`: qué jobs previos necesita este job.
- `only`: rama en la que ejecutar.

---

### Paso 4 — Push al repositorio

```bash
git add -A
git commit -m "Add: app, tests y pipeline CI/CD"
git push -u origin main
```

Si te pide credenciales, usa tu token de acceso de GitLab (no contraseña).

---

### Paso 5 — Verificar que se ejecuta pipeline automáticamente

1. En GitLab, ve a "CI/CD" → "Pipelines".
2. Deberías ver una pipeline en ejecución.

**NOTA:** Si aparece estado "pending" indefinidamente, significa que no hay runners configurados. Avanza al Paso 6.

---

### Paso 6 — Instalar GitLab Runner local

En terminal:

```bash
sudo docker run -d --name gitlab-runner --restart always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v gitlab-runner-config:/etc/gitlab-runner \
  gitlab/gitlab-runner:latest
```

---

### Paso 7 — Registrar runner con GitLab

1. En GitLab, ve a tu proyecto.
2. "Configuración" → "CI/CD" → "Runners".
3. Copia el token mostrado.

En terminal:

```bash
sudo docker exec -it gitlab-runner gitlab-runner register \
  --url https://gitlab.com/ \
  --token TU_TOKEN_AQUI \
  --executor docker \
  --docker-image python:3.11 \
  --description "Local Runner Demo" \
  --docker-volumes /var/run/docker.sock:/var/run/docker.sock
```

- Reemplaza `TU_TOKEN_AQUI` con el token copiado.
- Si es GitLab local, reemplaza `https://gitlab.com/` con tu URL.

---

### Paso 8 — Verificar que runner está activo

En GitLab, vuelve a "Runners". Deberías ver tu runner con estado verde.

---

### Paso 9 — Ejecutar pipeline nuevamente

1. En GitLab, ve a "CI/CD" → "Pipelines".
2. Clic en "Nueva canalización" (o espera a que se ejecute automáticamente en próximo push).
3. Rama: `main` (o `master`).
4. Clic "Ejecutar canalización".

Verás progreso visual:

```
build_job     (running/passed)
test_job      (waiting/running/passed)
report_job    (waiting/running/passed)
```

---

### Paso 10 — Inspeccionar logs detallados

1. Clic en la pipeline.
2. Clic en un job (ej. `test_job`).
3. Abre "Registro" (o "Salida de consola").

**Verás:**

```
========== TEST STAGE ==========
[... instalación de dependencias ...]
test_app.py::test_suma PASSED
test_app.py::test_resta PASSED
Tests completados
```

---

### Paso 11 — Explorar Merge Requests con CI/CD

1. En tu máquina, crea rama nueva:

```bash
git checkout -b feature/mejorar-app
```

2. Modifica `app.py` agregando nueva función:

```python
def multiplicacion(a, b):
    return a * b
```

3. Agrega test en `test_app.py`:

```python
def test_multiplicacion():
    assert multiplicacion(3, 4) == 12
```

4. Push:

```bash
git add -A
git commit -m "Add: función multiplicación con test"
git push -u origin feature/mejorar-app
```

5. En GitLab, verás sugerencia de "Crear Merge Request". Clic.
6. Crea el MR.
7. GitLab ejecutará pipeline automáticamente en MR.
8. Si todo pasa, podrás hacer merge desde GitLab.

---

## 5) Evidencias a entregar (capturas)

1. Repositorio GitLab creado con archivos.
2. Pipeline ejecutándose con 3 jobs visibles.
3. Status "Passed" en los 3 jobs.
4. Logs del job `test_job` mostrando tests con PASSED.
5. (Opcional) Merge Request con pipeline ejecutándose.

---

## 6) Errores frecuentes y soluciones

1. **Pipeline pending indefinidamente**  
   No hay runners. Instala GitLab Runner y regístralo (pasos 6-7).

2. **401 Unauthorized al registrar runner**  
   Token inválido. Copia nuevamente desde GitLab.

3. **Job falla por `module not found`**  
   Wheel no instaladas. Agrega `pip install wheel` en stage build.

4. **Docke can't pull image**  
   Verifica conexión a internet y permisos de runner.

5. **Merge Request no corre pipeline**  
   Verifica rama está en sección `only:` del `.gitlab-ci.yml`.

---

## 7) Criterio de éxito de la práctica

La práctica se considera completada cuando:

- Tienes repositorio GitLab con proyecto funcional.
- `.gitlab-ci.yml` define 3 stages (build, test, report).
- Pipeline ejecuta exitosamente todos los jobs.
- Puedes leer logs detallados de cada job.
- Entiendes diferencia entre stages y jobs paralelos.

---

## 8) Pasos siguientes

- Agrega stage de "deploy" (trabajado en Módulo 5).
- Configura variables protegidas para datos sensibles.
- Explora artifacts y cómo pasar archivos entre jobs.
- Integra validación de calidad con herramientas adicionales.
