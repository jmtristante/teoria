# Módulo 5 — Teoría: Pipelines CI/CD Completas para Big Data

## Objetivo del módulo

En este módulo vas a aprender a diseñar pipelines de integración y entrega continua completas, de principio a fin. Aprenderás qué etapas son necesarias, cómo manejar dependencias y artefactos, qué estrategias de despliegue existen y cómo gestionar configuración en entornos distintos (desarrollo, test, producción).

---

## Qué debes saber al terminar

Al finalizar este módulo deberías poder:

1. Diseñar una pipeline completa con todas sus etapas (clone, build, test, package, deploy).
2. Gestionar dependencias Python de forma reproducible.
3. Empaquetar y versionar artefactos correctamente.
4. Entender y elegir entre estrategias de despliegue.
5. Configurar variables por entorno sin hardcodear valores.
6. Manejar secretos de forma segura.

---

## 5.1 Diseño de pipelines completas para Big Data

### 5.1.1 Anatomía de una pipeline end-to-end

Una pipeline productiva tiene estructura clara con etapas que avanzan de forma lineal:

```
Clone (checkout) → Build (preparación) → Test (validación) 
→ Package (empaquetar) → Deploy (despliegue)
```

Cada etapa tiene un objetivo específico y genera artefactos o información que usa la siguiente.

### 5.1.2 Etapa 1: Clone (Checkout)

**Objetivo:** obtener el código más reciente del repositorio.

**Tareas típicas:**

- Clone del repositorio Git.
- Checkout de rama/commit específico.
- Verificar integridad del código.

**En Jenkins/GitLab:** se hace automático generalmente. Si deseas control manual:

```groovy
// Jenkins
stage('Clone') {
  steps {
    checkout scm
  }
}
```

```yaml
# GitLab
clone_job:
  stage: clone
  script:
    - git clone $CI_REPOSITORY_URL --branch $CI_COMMIT_REF_NAME
```

**Artefacto:** código fuente descargado.

### 5.1.3 Etapa 2: Build (Preparación del entorno)

**Objetivo:** preparar el entorno y resolver dependencias.

**Tareas:**

- Instalar dependencias (pip, npm, etc.).
- Compilar código si aplica.
- Resolver versiones específicas de librerías.

**En Python, gestión de dependencias:**

El archivo `requirements.txt` es crucial. Debe versionarse y fijarse versiones exactas:

```
pytest==7.4.3
pandas==2.2.3
pyspark==3.5.0
psycopg2-binary==2.9.10
```

**NO hacer esto (versiones flotantes):**

```
pytest
pandas
pyspark
```

Sin versiones fijas, dos builds en días distintos pueden instalar versiones incompatibles y fallar sin razón aparente.

**Ejemplo de stage build:**

```groovy
// Jenkins
stage('Build') {
  steps {
    sh '''
      python -m venv venv
      source venv/bin/activate
      pip install --upgrade pip
      pip install -r requirements.txt
    '''
  }
}
```

```yaml
# GitLab
build_job:
  stage: build
  image: python:3.11
  script:
    - pip install --upgrade pip
    - pip install -r requirements.txt
  artifacts:
    paths:
      - venv/
    expire_in: 1 hour
```

**Artefacto:** entorno con dependencias instaladas (o caché reutilizable).

### 5.1.4 Etapa 3: Test (Validación)

**Objetivo:** ejecutar validaciones automáticas (tests unitarios, integración, calidad de datos).

**Tipos de test en Big Data:**

- **Unitarios:** tests de funciones individuales.
- **Integración:** tests de componentes que interactúan.
- **Calidad de datos:** validaciones con herramientas como Great Expectations.

**Ejemplo con pytest:**

```groovy
// Jenkins
stage('Test') {
  steps {
    sh '''
      source venv/bin/activate
      pytest tests/ -v --tb=short
    '''
  }
}
```

```yaml
# GitLab
test_job:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v --tb=short
  artifacts:
    reports:
      junit: test-results.xml
```

**Criterio de éxito:** todos los tests pasan, cobertura mínima alcanzada.

**Artefacto:** reporte de tests (si falla, pipeline para).

### 5.1.5 Etapa 4: Package (Empaquetado)

**Objetivo:** generar artefacto versionado y redistributible.

En Big Data, esto puede ser:

- Imagen Docker de aplicación.
- Archivo JAR compilado.
- Código Python empaquetado en wheel.
- Script .zip con todas las dependencias.

**Empaquetado Docker (más común en producciones modernas):**

```groovy
// Jenkins
stage('Package') {
  steps {
    sh '''
      docker build -t miapp:${BUILD_NUMBER} .
      docker tag miapp:${BUILD_NUMBER} miapp:latest
    '''
  }
}
```

```yaml
# GitLab
package_job:
  stage: package
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

**Punto crítico:** el artefacto debe estar versionado (por commit, BUILD_NUMBER o release tag).

**Artefacto:** imagen Docker publicada en registry.

### 5.1.6 Etapa 5: Deploy (Despliegue)

**Objetivo:** ejecutar el artefacto en un entorno (dev, test o producción).

Este es el paso más crítico y varía según infraestructura.

**Deploy simple (local):**

```groovy
stage('Deploy Dev') {
  steps {
    sh '''
      docker stop miapp-dev || true
      docker rm miapp-dev || true
      docker run -d --name miapp-dev -p 8080:8080 miapp:latest
    '''
  }
}
```

**Estrategias de despliegue (cubierto en 5.1.7).**

---

### 5.1.7 Estrategias de despliegue

La forma en que pagas código nuevo en producción marca diferencia entre downtime y estabilidad.

#### Recreate (más simple, con downtime)

1. Parar versión anterior.
2. Arrancar nueva versión.

Ventaja: simple. Desventaja: servicio no disponible durante transición (segundos a minutos).

```yaml
deploy_recreate:
  script:
    - docker stop miapp || true
    - docker rm miapp || true
    - docker run -d --name miapp miapp:new
```

#### Rolling Update (reemplazo gradual)

Este patrón es especialmente útil cuando tienes múltiples servidores ejecutando tu aplicación. Imagina que tienes 4 instancias del mismo servicio corriendo. En lugar de parar todas y arrancar nuevas (lo que genera downtime), Rolling Update te permite:

1. Parar instancia 1, arrancar instancia 1 nueva.
2. Parar instancia 2, arrancar instancia 2 nueva.
3. Continuar con 3 y 4.

Durante todo el proceso, las instancias que todavía no fueron reemplazadas siguen sirviendo tráfico. La carga se distribuye automáticamente. Si la nueva versión falla, solo las instancias nuevas afectan; el rollback es detener el despliegue y dejar las viejas sirviendo.

Ventaja: sin downtime, rollback más fácil. Desventaja: requiere múltiples instancias y un load balancer que distribuya tráfico.

#### Blue-Green (dos entornos paralelos)

Esta estrategia es como tener dos salas de cine idénticas. La actual (Blue) está funcionando normalmente con clientes. Preparas la otra (Green) con la nueva versión.

1. **Blue** = dos instancias con versión v1.2.2 sirviendo tráfico real.
2. **Green** = dos instancias con versión v1.2.3, sin tráfico.
3. Validas que Green funciona correctamente (tests en vivo, checks de salud).
4. **Switch:** load balancer redirige TODOS los clientes de Blue a Green instantáneamente.
5. **Si falla:** vuelves a dirigir al load balancer a Blue. Rollback en segundos.

Ventaja principal: el switch es instantáneo y el rollback es trivial. Si algo falla en Green, simplemente dices "olvida Green, vuelve a Blue" y literalmente volvemos a estado conocido en segundos, sin degradación gradual.

Desventaja: cuesta dinero double. Necesitas infraestructura para dos entornos completos ejecutándose simultáneamente (aunque Blue pueda ser más pequeño).

#### Canary (despliegue con riesgo controlado)

Esta técnica viene de un dicho histórico: "canary in a coal mine". Los mineros llevaban canarios en jaulas como detector temprano de gases venenosos. Si el canario se desmayaba = tiempo de irse del túnel.

En despliegues, la idea es similar: liberas código nuevo a un pequeño % de usuarios para detectar problemas antes de que afecten a todo el mundo.

Fases típicas de un canary:

1. **5% de tráfico** → envías usuarios a v1.2.3 (versión nueva). El 95% sigue en v1.2.2 (versión anterior).
2. Monitoreas métricas clave: tasa de errores HTTP 5xx, latencia p95, uso de CPU/memoria. Si v1.2.3 se comporta igual que v1.2.2 por 30 minutos, avanzas.
3. **25% de tráfico** → más usuarios prueban v1.2.3. Si métricas siguen bien, siguiente paso.
4. **50% de tráfico** → ya es mitad y mitad. En este punto tienes mucha confianza.
5. **100%** → todos en v1.2.3. Si algo falla después, at least sabes que la primera mitad estuvo bien.

Si en cualquier punto ves picos de errores o latencia anómala en la cohorte canary, puedes ejecutar un rollback automático: retroceder a v1.2.2 para ese grupo (y todos si decides detener).

Ventaja: riesgo muy bajo. Problemas se detectan con 5-10% de usuarios, no 100%. Rollback automático si va mal. Desventaja: es lo más complejo de implementar. Requiere monitoreo en tiempo real, señales claras de "ok/no ok", y lógica de tráfico condicional (HTTP header routing, cookie-based sessions, etc).

**Recomendación para formativos iniciales:** Recreate o Rolling Update. Blue-Green y Canary son opcionales (Módulo 7+).

### 5.1.8 Gestión de dependencias Python

En proyectos serios, reproducibilidad de dependencias es crítica. Imagina esto:

- **Martes**: Builds de teste con `pandas>=2.0` (ahora hay v2.2.3, v2.1.0, v2.0.5).
- **Jueves**: Alguien publica pandas v2.2.5 con un fix.
- **Viernes**: Buildo de prod usa `pandas>=2.0`, que ahora resuelve a v2.2.5 (distinto de martes).
- **Resultado:** código corriendo en prod es distinto del que se testeó.

O peor: alguien publica `pandas v3.0` con cambios breaking. De repente, tu build rompe, pero el código no cambió.

Solución: **tres capas de requirements**

**Capa 1: Development (flexible para experimentos)**

`requirements-dev.txt` - para desarrollo local, permite rangos:

```
pandas>=2.0,<3.0
pytest>=7.0
black>=23.0
pylint>=3.0
```

Cuando estás desarrollando, está bien que se auto-actualicen. Quieres probar nuevas versiones, encontrar incompatibilidades temprano.

**Capa 2: Production (versiones fijas, pinned)**

`requirements-prod.txt` - versiones exactas, sin rangos:

```
pandas==2.2.3
numpy==1.26.0
pyspark==3.5.0
psycopg2-binary==2.9.10
boto3==1.28.45
```

En producción, no quieres sorpresas. Exactamente v2.2.3, no "lo que sea que esté disponible".

**Capa 3: Lock file (hash de seguridad)**

En pipeline, generamos lock file con hashes de los paquetes exactos:

```bash
pip freeze > requirements-lock.txt
```

Resultado:

```
pandas==2.2.3 --hash=sha256:abc123def456...
numpy==1.26.0 --hash=sha256:xyz789uvw012...
```

**En pipeline, instalamos desde lock:**

```bash
# Etapa Build
pip install -r requirements-lock.txt

# Esto fuerza exactamente pandas==2.2.3 y valida hash.
# Si alguien publicó un paquete falso con mismo nombre/versión, el hash no coincide, falla.
```

**Resultado:** 

- Build de martes y build de viernes usan EXACTAMENTE las mismas versiones.
- Si falla algo en producción, sabes que fue por lógica, no por cambio de dependencia.
- Reproducibilidad completa.

### 5.1.9 Versionado de artefactos

Cada artefacto publicado debe ser **identificable y rastreable**. Esto importa más de lo que suena.

Imagina este escenario: son las 3 AM, tu jefe te llama. "Algo rompió hace una hora. Usuarios reportan errores. ¿Qué versión está corriendo en prod?" Si no tienes versionado claro, estás jodido. No sabes qué código está ejecutándose, no sabes a qué commit corresponde, no sabes qué cambios incluye.

Con versionado correcto:

```
miapp:v1.2.3               # versión semántica (release formales)
miapp:dev-{build_number}   # versión de desarrollo (cada build)
miapp:{commit_short_hash}  # trazabilidad: exactamente qué commit
miapp:prod-{date}          # producción con fecha (para auditoría)
```

Combinar estrategias:

```yaml
# GitLab CI example
package_job:
  script:
    - export VERSION="${CI_COMMIT_TAG:-v1.2.${CI_PIPELINE_ID}}"
    - export SHORT_HASH="${CI_COMMIT_SHORT_SHA}"
    - docker build -t $CI_REGISTRY_IMAGE:$VERSION .
    - docker tag $CI_REGISTRY_IMAGE:$VERSION $CI_REGISTRY_IMAGE:$SHORT_HASH
    - docker tag $CI_REGISTRY_IMAGE:$VERSION $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:$VERSION
    - docker push $CI_REGISTRY_IMAGE:$SHORT_HASH
```

Resultado: depués, tienes un audit trail perfecto.

```bash
# 3 AM, tras el incidente
$ docker inspect miapp:prod-running | grep Image
"Image": "$CI_REGISTRY_IMAGE:1a2b3c4d"

# Buscas en GitLab CI
$ git show 1a2b3c4d --oneline
commit 1a2b3c4d Author: juan@company.com
"Fix login bug in auth module"

# Ahora sabes qué cambio están ejecutando. Investigas ese commit, identifica el bug.
```

Sin versionado claro, esto es imposible.

### 5.1.10 Rollback y recuperación

Si un despliegue es malo, necesitas revertir rápido.

**Rollback manual:**

```bash
# Volver a versión anterior
docker pull miapp:v1.2.2
docker stop miapp && docker rm miapp
docker run -d --name miapp miapp:v1.2.2
```

**Rollback automático (Kubernetes):**

```bash
kubectl rollout undo deployment/miapp
```

**Rollback con Blue-Green:**

Switch load balancer de Green a Blue instantáneamente.

**Punto clave:** si no tienes versionado de artefactos, rollback es imposible.

---

## 5.2 Gestión de configuración por entornos

### 5.2.1 Problema: hardcodear valores es peligroso

```python
# MALO (NO HACER)
DB_HOST = "prod-db.example.com"
DB_USER = "admin"
DB_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"
```

Problemas:

- Secretos visibles en código versionado.
- Imposible reutilizar código en dev/test/prod sin cambiar.
- Si alguien clona repo, tiene acceso a credenciales reales.

### 5.2.2 Solución: variables de entorno

Externalizar configuración en variables que pasan en tiempo de ejecución:

```python
import os

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
API_KEY = os.getenv("API_KEY")
```

Ahora el código no cambia. Lo que cambia es cómo lanzo el contenedor:

**Dev:**
```bash
docker run -e DB_HOST=localhost -e DB_USER=dev ...
```

**Prod:**
```bash
docker run -e DB_HOST=prod-db.example.com -e DB_USER=prod_user ...
```

### 5.2.3 Archivos de configuración (.env, config.yaml)

Para manejar muchas variables, archivos de configuración son más claros:

**Opción 1: `.env` (simple)**

```
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_dev
LOG_LEVEL=DEBUG
```

En Python:

```python
from dotenv import load_dotenv
import os

load_dotenv()
app_env = os.getenv("APP_ENV")
```

**Opción 2: `config.yaml` (más estructurado)**

```yaml
development:
  db:
    host: localhost
    port: 5432
    name: myapp_dev
  logging:
    level: DEBUG

production:
  db:
    host: prod-db.example.com
    port: 5432
    name: myapp_prod
  logging:
    level: ERROR
```

En Python:

```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

env = os.getenv("APP_ENV", "development")
db_config = config[env]["db"]
```

### 5.2.4 Variables por entorno en Jenkins/GitLab

**Jenkins:**

1. Job → "Configurar".
2. "Parámetros con valor por defecto".
3. Agregar parámetro `ENVIRONMENT` con valores: `dev`, `test`, `prod`.
4. En pipeline, usar variable:

```groovy
stages {
  stage('Deploy') {
    steps {
      sh '''
        if [ "$ENVIRONMENT" = "prod" ]; then
          docker run -e DB_HOST=prod-db ...
        else
          docker run -e DB_HOST=dev-db ...
        fi
      '''
    }
  }
}
```

**GitLab:**

```yaml
variables:
  DB_HOST_DEV: "dev-db.local"
  DB_HOST_PROD: "prod-db.example.com"

deploy_dev:
  stage: deploy
  environment: development
  variables:
    DB_HOST: $DB_HOST_DEV
  script:
    - docker run -e DB_HOST=$DB_HOST myapp:latest
  only:
    - develop

deploy_prod:
  stage: deploy
  environment: production
  variables:
    DB_HOST: $DB_HOST_PROD
  script:
    - docker run -e DB_HOST=$DB_HOST myapp:latest
  only:
    - main
```

### 5.2.5 Gestión de secretos (credenciales, tokens, contraseñas)

**Regla de oro: nunca en repositorio, nunca en logs, nunca hardcoded.**

Hardcodear un password en código es lo opuesto a CI/CD serio. Si commiteas `DB_PASSWORD="prod_123"` en el Dockerfile:

1. **Seguridad:** cualquiera con acceso al repo (incluso ex-empleados con acceso histórico a Git) ve la credencial.
2. **Auditoría:** si cambian password, tienes que cambiar código y re-desplegar. Pesadilla.
3. **Compliance:** violarías GDPR, HIPAA u otros estándares que exigen rotación de secretos.

La solución: guardar secretos fuera del código, inyectarlos en tiempo de ejecución.

**Jenkins: Credentials Binding**

1. En Jenkins, ir a "Administrar Jenkins" → "Credenciales" (o "Manage Credentials").
2. Crear credencial: Username + Password, o Secret text (para API tokens).
3. Cifrada con la clave maestra de Jenkins (no plain text).

En pipeline Jenkinsfile:

```groovy
stage('Deploy a Producción') {
  steps {
    withCredentials([usernamePassword(credentialsId: 'db-prod-creds', 
                                       usernameVariable: 'DB_USER', 
                                       passwordVariable: 'DB_PASSWORD')]) {
      sh '''
        docker run -e DB_USER=$DB_USER -e DB_PASSWORD=$DB_PASSWORD \
                   -d myapp:latest
      '''
    }
  }
}
```

Flujo internamente:

1. Jenkins tiene almacenada la credencial `db-prod-creds` en su base de datos (cifrada).
2. Al ejecutar `withCredentials`, Jenkins desencripta temporalmente.
3. Asigna valores a variables de entorno `DB_USER` y `DB_PASSWORD`.
4. El script de shell accede a `$DB_USER` y `$DB_PASSWORD`.
5. Jenkins **automaticamente enmascara los valores** en logs (si imprimías `echo $DB_PASSWORD`, verías `****`).
6. Después del `withCredentials`, las variables se borran de memoria.

**GitLab: Protected Variables y Masked Variables**

1. En tu proyecto, ir a "Settings" → "CI/CD" → "Variables".
2. Crear variable: nombre `DB_PASSWORD`, valor `prod_secure_password_here`.
3. Marcar checkbox "Protected" → la variable solo existe en pipelines que corren en ramas protegidas (main, release/).
4. Marcar checkbox "Masked" → GitLab oculta el valor en logs (muestra `*****`).

En `.gitlab-ci.yml`:

```yaml
deploy_prod:
  stage: deploy
  environment: production
  script:
    - docker run -e DB_PASSWORD=$DB_PASSWORD \
                 -d myapp:latest
  only:
    - main
```

Flujo:

1. Pipeline se ejecuta en rama `main` (protegida).
2. Variable `DB_PASSWORD` se inyecta en el job.
3. El script la usa (`$DB_PASSWORD`).
4. En los logs vistos en UI, GitLab automáticamente reemplaza `prod_secure_password_here` con `*****`.
5. Solo Jenkins admin (o dueño del repo) puede ver el valor real en Settings → CI/CD.

**Comparación:**

| Aspecto | Jenkins | GitLab |
|--------|---------|--------|
| Almacenamiento | Base de datos Jenkins (local) | GitLab database |
| Cifrado | Clave maestra de Jenkins | Clave de GitLab |
| Scope | Por credencial (nombre) | Por proyecto + variable |
| Protección por rama | Manual (en Jenkinsfile) | Automática (Protected) |
| Ícono de ocultación en logs | Sí (mascarado) | Sí (mascarado) |
| Rotación | Cambiar credencial en Jenkins UI | Cambiar valor en Variables |

**Mejor práctica:** rotación regular de secretos. No usar la misma contraseña de prod por 2 años.

### 5.2.6 Patrones comunes de configuración

**Patrón 1: por rama**

```
develop branch → deploy a DEV
release/* branch → deploy a TEST/STAGING
main branch → deploy a PROD
```

**Patrón 2: por tag**

```
git tag v1.2.3
→ Deploy automático a PROD
```

**Patrón 3: por entorno explícito**

```
Pipeline job con parámetro: ENVIRONMENT = dev/test/prod
Usuario elige al ejecutar
```

### 5.2.7 Buenas prácticas en configuración

1. **Versionada:** `.env` / `config.yaml` en repositorio, sin secretos.
2. **Secretos externos:** credenciales en Jenkins/GitLab, no en repo.
3. **Consistencia:** misma estructura de variables en dev/test/prod.
4. **Documentación:** README con qué variables se requieren.
5. **Validación temprana:** pipeline falla pronto si variable falta.

El punto 5 es crítico. Si faltan variables, **quieres saberlo al inicio del pipeline, no después de 15 minutos de build**.

Ejemplo de validación en Jenkins:

```groovy
stage('Validate Config') {
  steps {
    sh '''
      set -e  # Exit on first error
      echo "Checking required variables..."
      [ -n "$DB_HOST" ] || { echo "ERROR: DB_HOST"; exit 1; }
      [ -n "$DB_USER" ] || { echo "ERROR: DB_USER"; exit 1; }
      [ -n "$API_KEY" ] || { echo "ERROR: API_KEY"; exit 1; }
      echo "All variables present ✓"
    '''
  }
}
```

En GitLab:

```yaml
validate_config:
  stage: validate
  script:
    - |
      required_vars="DB_HOST DB_USER API_KEY"
      for var in $required_vars; do
        if [ -z "${!var}" ]; then
          echo "ERROR: $var not set"
          exit 1
        fi
      done
      echo "All variables present ✓"
```

**Beneficio:** si algo no está configurado, **el pipeline falla al minuto 1**, no al minuto 45 cuando ya llevó tiempo compilando.

---

## Flujo completo de ejemplo: App Python a Producción

**Escenario:** desarrollador hace push a rama `develop`.

1. **Clone:** Jenkins/GitLab detecta push.
2. **Build:** instala `requirements.txt`, Python env listo.
3. **Test:** corre pytest, valida datos con expectations.
4. **Package:** construye imagen Docker, etiquetada `dev-{build_number}`.
5. **Deploy Dev:** corre contenedor en servidor dev con variables DEV.

**Escenario:** desarrollador hace tag `v1.2.3` en rama `main`.

1. **Clone:** detecta tag.
2. **Build:** igual.
3. **Test:** igual.
4. **Package:** construye imagen etiquetada `v1.2.3` y `latest`.
5. **Deploy Prod:** corre imagen en producción con variables PROD + health checks.

**Si falla en Deploy Prod:**

- Pipeline detiene.
- Equipo recibe alerta.
- Rollback: `docker run miapp:v1.2.2`.
- Investigar qué salió mal.
- Fix código, nuevo tag, reintentar.

---

## Resumen final

El Módulo 5 te enseña a pensar en pipelines como **procesos end-to-end con rigor**.

De desarrollador solitario con script manual, pasas a:
- Pipeline reproducible.
- Artefactos versionados.
- Configuración por entorno.
- Despliegues seguros con rollback.
- Trazabilidad completa.

Eso es lo que hace CI/CD real.
