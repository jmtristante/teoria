# Práctica 5.2: Gestión de Configuración en GitLab CI/CD

**Duración estimada:** 50-60 minutos  
**Requisitos previos:** Práctica 5.1 completada. GitLab corriendo.

---

## Objetivo

Aprender a gestionar configuración de forma profesional en GitLab CI/CD, separando código de configuración según entornos (development, staging, production), usando:

1. Variables de entorno en la aplicación.
2. Variables de proyecto y grupo en GitLab.
3. Variables protegidas y enmascaradas para secretos.
4. Environments de GitLab para tracking de deployments.
5. Configuración dinámica sin hardcodear valores en el pipeline.

**Enfoque:** Esta práctica usa GitLab exclusivamente para demostrar sus capacidades avanzadas de gestión de configuración y mejores prácticas de seguridad.

---

## Conceptos Base (5 min)

### Problema: Hardcoding vs. Configuración Externa

❌ **Incorrecto (hardcoded):**

```python
DB_HOST = "prod-db.internal"  # ← Valor fijo en código
API_KEY = "sk_prod_abc123"    # ← Secreto expuesto
MAX_CONNECTIONS = 100         # ← Sin flexibilidad
```

**Problemas:**
- Mismo código no puede correr en diferentes entornos
- Secretos expuestos en repositorio
- Cambio de config requiere rebuild completo
- Violación de principio "12-factor app"

✅ **Correcto (variables de entorno):**

```python
DB_HOST = os.getenv("DB_HOST", "localhost")
API_KEY = os.getenv("API_KEY")  # Sin default para secretos
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "10"))
```

**Ventajas:**
- Misma imagen Docker corre en cualquier entorno
- Secretos inyectados en runtime, nunca en código
- Config cambia sin rebuild
- Cumple estándar "12-factor app"

### GitLab CI/CD Variables - Jerarquía

GitLab proporciona variables en múltiples niveles (de mayor a menor prioridad):

1. **Trigger variables** (manual/API)
2. **Job-level variables** (en `.gitlab-ci.yml`)
3. **Project variables** (Settings > CI/CD > Variables)
4. **Group variables** (heredadas de grupo padre)
5. **Instance variables** (nivel servidor GitLab)

**Tipos especiales:**
- **Protected:** Solo disponibles en ramas/tags protegidos (main, tags de release)
- **Masked:** No aparecen en logs (para secretos)
- **Environment scope:** Específicas de un environment (development, production, etc.)

---

## PARTE 1: Actualizar Aplicación con Configuración (10 min)

### Paso 1.1: Crear app mejorada con configuración

Crea un nuevo directorio o usa el de la práctica anterior:

```bash
cd ~/formacion-cd
mkdir -p app-config-gitlab && cd app-config-gitlab
```

**app.py:**

```python
#!/usr/bin/env python3
"""
Aplicación con configuración por entorno.
Demuestra separación de código y configuración.
"""
import os
import sys
import json
from datetime import datetime

class Config:
    """Configuración centralizada leída desde variables de entorno."""
    
    # Configuración de aplicación
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_VERSION = os.getenv("CI_COMMIT_SHORT_SHA", "local")
    
    # Configuración de base de datos
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "appdb")
    DB_USER = os.getenv("DB_USER", "app")
    DB_PASSWORD = os.getenv("DB_PASSWORD")  # Sin default - debe estar definido
    
    # Configuración de aplicación
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "10"))
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "false").lower() == "true"
    
    # Configuración de features
    FEATURE_ANALYTICS = os.getenv("FEATURE_ANALYTICS", "false").lower() == "true"
    FEATURE_NOTIFICATIONS = os.getenv("FEATURE_NOTIFICATIONS", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Valida que configuración crítica esté presente."""
        errors = []
        
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD no está configurado")
        
        if cls.APP_ENV not in ["development", "staging", "production"]:
            errors.append(f"APP_ENV inválido: {cls.APP_ENV}")
        
        if errors:
            print("❌ Errores de configuración:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    @classmethod
    def print_config(cls, hide_secrets=True):
        """Imprime configuración actual (ocultando secretos)."""
        config = {
            "environment": cls.APP_ENV,
            "version": cls.APP_VERSION,
            "database": {
                "host": cls.DB_HOST,
                "port": cls.DB_PORT,
                "name": cls.DB_NAME,
                "user": cls.DB_USER,
                "password": "***" if hide_secrets and cls.DB_PASSWORD else cls.DB_PASSWORD
            },
            "application": {
                "log_level": cls.LOG_LEVEL,
                "max_connections": cls.MAX_CONNECTIONS,
                "cache_enabled": cls.ENABLE_CACHE
            },
            "features": {
                "analytics": cls.FEATURE_ANALYTICS,
                "notifications": cls.FEATURE_NOTIFICATIONS
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        return config

def simulate_database_connection():
    """Simula conexión a base de datos."""
    print(f"\n🔌 Intentando conectar...")
    print(f"   Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"   Database: {Config.DB_NAME}")
    print(f"   User: {Config.DB_USER}")
    
    # En una app real, aquí harías: psycopg2.connect(...)
    print("✅ Conexión simulada exitosa")

def process_data(text):
    """Procesa datos usando la configuración."""
    result = text.upper()
    
    if Config.ENABLE_CACHE:
        print("📦 Resultado cacheado (cache habilitado)")
    
    if Config.FEATURE_ANALYTICS:
        print("📊 Evento enviado a analytics")
    
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando aplicación")
    print("=" * 60)
    
    # Validar configuración crítica
    Config.validate()
    
    # Mostrar configuración
    print("\n📋 Configuración actual:")
    print(json.dumps(Config.print_config(), indent=2))
    
    # Simular operaciones
    simulate_database_connection()
    
    print("\n⚙️  Procesando datos...")
    result = process_data("config management demo")
    print(f"   Resultado: {result}")
    
    print("\n" + "=" * 60)
    print(f"✅ Aplicación ejecutada exitosamente en: {Config.APP_ENV}")
    print("=" * 60)
```

### Paso 1.2: Crear archivo de tests

**tests/test_app.py:**

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import process_data, Config

def test_process_data():
    """Test procesamiento básico."""
    result = process_data("test")
    assert result == "TEST"

def test_config_defaults():
    """Test valores por defecto."""
    # En tests, variables no están definidas
    assert Config.APP_ENV in ["development", "staging", "production", "test"]
    assert Config.DB_HOST is not None
    assert Config.LOG_LEVEL is not None
```

### Paso 1.3: Crear archivos de documentación de configuración

**.env.example:**

```bash
# Ejemplo de variables de entorno requeridas
# NUNCA commitear archivo .env con valores reales

# === Identificación de Aplicación ===
APP_ENV=development              # development | staging | production
APP_VERSION=1.0.0

# === Base de Datos ===
DB_HOST=localhost
DB_PORT=5432
DB_NAME=appdb
DB_USER=app
DB_PASSWORD=secret123            # ⚠️ En GitLab: Variable protegida y enmascarada

# === Configuración de Aplicación ===
LOG_LEVEL=DEBUG                  # DEBUG | INFO | WARNING | ERROR
MAX_CONNECTIONS=10
ENABLE_CACHE=false               # true | false

# === Feature Flags ===
FEATURE_ANALYTICS=false
FEATURE_NOTIFICATIONS=true
```

**CONFIG.md:**

```markdown
# Configuración de la Aplicación

## Variables de Entorno Requeridas

### Críticas (deben estar definidas)
- `DB_PASSWORD`: Contraseña de base de datos

### Por Entorno

#### Development
- `APP_ENV=development`
- `DB_HOST=localhost`
- `LOG_LEVEL=DEBUG`
- `ENABLE_CACHE=false`

#### Staging
- `APP_ENV=staging`
- `DB_HOST=staging-db.internal`
- `LOG_LEVEL=INFO`
- `ENABLE_CACHE=true`

#### Production
- `APP_ENV=production`
- `DB_HOST=prod-db.internal`
- `LOG_LEVEL=ERROR`
- `ENABLE_CACHE=true`
- `FEATURE_ANALYTICS=true`

## Configuración en GitLab

Variables se configuran en: **Settings > CI/CD > Variables**

### Variables Protegidas
- `DB_PASSWORD` (masked, protected)
- `API_KEY` (masked, protected)

### Variables por Environment
Usar "Environment scope" para definir por entorno.
```

### Paso 1.4: Actualizar requirements y configuración

**requirements.txt:**

```
pytest==7.4.3
```

**.gitignore:**

```
__pycache__/
*.pyc
.pytest_cache/
venv/
.env
.env.local
.env.*.local
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY tests/ tests/

# Variables de entorno se inyectarán en runtime
ENV APP_ENV=development

CMD ["python", "app.py"]
```

### Paso 1.5: Test local (opcional)

```bash
# Crear .env local solo para testing
cat > .env << 'EOF'
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=testdb
DB_USER=testuser
DB_PASSWORD=testpass123
LOG_LEVEL=DEBUG
MAX_CONNECTIONS=5
ENABLE_CACHE=false
FEATURE_ANALYTICS=false
EOF

# Exportar variables (solo para test)
set -a && source .env && set +a

# Test
python app.py

# Limpiar
rm .env
```

### Paso 1.6: Inicializar repositorio

```bash
cd ~/formacion-cd/app-config-gitlab
git init
git add .
git commit -m "Initial commit: app with environment config"
```

### ✓ Checkpoint 1: App lista con configuración externa

---

## PARTE 2: Configurar Variables en GitLab (15 min)

### Paso 2.1: Crear proyecto en GitLab

1. GitLab: `http://localhost:81` (o tu URL)
2. "New project" → "Create blank project"
3. Name: `app-config-gitlab`
4. Visibility: Private (recomendado para apps con config)
5. Click "Create project"

### Paso 2.2: Pushear código

```bash
cd ~/formacion-cd/app-config-gitlab

# Configurar remote
git remote add origin http://localhost:81/root/app-config-gitlab.git

# Push
git push -u origin main
```

### Paso 2.3: Configurar Variables de Proyecto

Navega a: **Settings > CI/CD > Variables** → Click "Add variable"

#### Variables Comunes (todas los environments)

| Key | Value | Type | Protected | Masked | Environment scope |
|-----|-------|------|-----------|--------|-------------------|
| `DB_PORT` | `5432` | Variable | ❌ | ❌ | All |
| `DB_NAME` | `appdb` | Variable | ❌ | ❌ | All |
| `DB_USER` | `app` | Variable | ❌ | ❌ | All |

#### Variables por Environment (Development)

| Key | Value | Type | Protected | Masked | Environment scope |
|-----|-------|------|-----------|--------|-------------------|
| `APP_ENV` | `development` | Variable | ❌ | ❌ | development |
| `DB_HOST` | `localhost` | Variable | ❌ | ❌ | development |
| `DB_PASSWORD` | `dev_pass_123` | Variable | ❌ | ✅ | development |
| `LOG_LEVEL` | `DEBUG` | Variable | ❌ | ❌ | development |
| `MAX_CONNECTIONS` | `10` | Variable | ❌ | ❌ | development |
| `ENABLE_CACHE` | `false` | Variable | ❌ | ❌ | development |
| `FEATURE_ANALYTICS` | `false` | Variable | ❌ | ❌ | development |
| `FEATURE_NOTIFICATIONS` | `true` | Variable | ❌ | ❌ | development |

#### Variables por Environment (Staging)

| Key | Value | Type | Protected | Masked | Environment scope |
|-----|-------|------|-----------|--------|-------------------|
| `APP_ENV` | `staging` | Variable | ✅ | ❌ | staging |
| `DB_HOST` | `staging-db.internal` | Variable | ✅ | ❌ | staging |
| `DB_PASSWORD` | `staging_secure_pass` | Variable | ✅ | ✅ | staging |
| `LOG_LEVEL` | `INFO` | Variable | ❌ | ❌ | staging |
| `MAX_CONNECTIONS` | `50` | Variable | ❌ | ❌ | staging |
| `ENABLE_CACHE` | `true` | Variable | ❌ | ❌ | staging |
| `FEATURE_ANALYTICS` | `true` | Variable | ❌ | ❌ | staging |

#### Variables por Environment (Production)

| Key | Value | Type | Protected | Masked | Environment scope |
|-----|-------|------|-----------|--------|-------------------|
| `APP_ENV` | `production` | Variable | ✅ | ❌ | production |
| `DB_HOST` | `prod-db.internal` | Variable | ✅ | ❌ | production |
| `DB_PASSWORD` | `prod_super_secure_password_2024` | Variable | ✅ | ✅ | production |
| `LOG_LEVEL` | `ERROR` | Variable | ✅ | ❌ | production |
| `MAX_CONNECTIONS` | `100` | Variable | ✅ | ❌ | production |
| `ENABLE_CACHE` | `true` | Variable | ✅ | ❌ | production |
| `FEATURE_ANALYTICS` | `true` | Variable | ✅ | ❌ | production |

**Notas importantes:**

- **Protected (✅):** Solo disponible en ramas/tags protegidos (main, v*.*)
- **Masked (✅):** Valor oculto en logs (usar para contraseñas)
- **Environment scope:** Liga variable a un environment específico

### Paso 2.4: Proteger rama main (necesario para variables protegidas)

1. **Settings > Repository > Protected branches**
2. Branch: `main`
3. Allowed to merge: `Maintainers`
4. Allowed to push: `No one` (o `Maintainers`)
5. Click "Protect"

### ✓ Checkpoint 2: Variables configuradas en GitLab

---

## PARTE 3: Pipeline con Environments (15 min)

### Paso 3.1: Crear .gitlab-ci.yml con environments

**.gitlab-ci.yml:**

```yaml
stages:
  - build
  - test
  - deploy

# Variables globales (NO incluir secretos aquí)
variables:
  DOCKER_REGISTRY: "localhost:5000"
  APP_NAME: "app-config"

# Template para construir imagen
.build_template:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - |
      echo "Building Docker image..."
      IMAGE="${DOCKER_REGISTRY}/${APP_NAME}:${CI_COMMIT_SHORT_SHA}"
      docker build -t "${IMAGE}" .
      echo "Image built: ${IMAGE}"
  tags:
    - docker

# Template para tests
.test_template:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install --no-cache-dir -r requirements.txt
  script:
    - |
      echo "Running tests..."
      python -m pytest tests/ -v
      echo "Tests passed"

# Template para deploy
.deploy_template:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - |
      echo "Deploying to ${CI_ENVIRONMENT_NAME}..."
      IMAGE="${DOCKER_REGISTRY}/${APP_NAME}:${CI_COMMIT_SHORT_SHA}"
      CONTAINER="${APP_NAME}-${CI_ENVIRONMENT_SLUG}"

      docker stop "${CONTAINER}" 2>/dev/null || true
      docker rm "${CONTAINER}" 2>/dev/null || true

      docker run -d \
        --name "${CONTAINER}" \
        -e APP_ENV="${APP_ENV}" \
        -e DB_HOST="${DB_HOST}" \
        -e DB_PORT="${DB_PORT}" \
        -e DB_NAME="${DB_NAME}" \
        -e DB_USER="${DB_USER}" \
        -e DB_PASSWORD="${DB_PASSWORD}" \
        -e LOG_LEVEL="${LOG_LEVEL}" \
        -e MAX_CONNECTIONS="${MAX_CONNECTIONS}" \
        -e ENABLE_CACHE="${ENABLE_CACHE}" \
        -e FEATURE_ANALYTICS="${FEATURE_ANALYTICS}" \
        -e FEATURE_NOTIFICATIONS="${FEATURE_NOTIFICATIONS:-true}" \
        -e CI_COMMIT_SHORT_SHA="${CI_COMMIT_SHORT_SHA}" \
        "${IMAGE}"

      echo "Waiting for container startup..."
      sleep 3
      echo "Container logs:"
      docker logs "${CONTAINER}"
      echo "Deploy completed in ${CI_ENVIRONMENT_NAME}"

# ========================================
# JOBS - BUILD
# ========================================

build:
  extends: .build_template
  only:
    - main
    - develop
    - /^release\/.*$/

# ========================================
# JOBS - TEST
# ========================================

test:
  extends: .test_template
  only:
    - main
    - develop
    - /^release\/.*$/

# ========================================
# JOBS - DEPLOY
# ========================================

deploy:development:
  extends: .deploy_template
  environment:
    name: development
    on_stop: stop:development
  only:
    - develop
  when: manual

deploy:staging:
  extends: .deploy_template
  environment:
    name: staging
    on_stop: stop:staging
  only:
    - main
  when: manual

deploy:production:
  extends: .deploy_template
  environment:
    name: production
    on_stop: stop:production
  only:
    - tags
  when: manual

# ========================================
# JOBS - STOP (cleanup)
# ========================================

stop:development:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker stop ${APP_NAME}-development || true
    - docker rm ${APP_NAME}-development || true
    - echo "🛑 Development environment stopped"
  environment:
    name: development
    action: stop
  when: manual
  only:
    - develop

stop:staging:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker stop ${APP_NAME}-staging || true
    - docker rm ${APP_NAME}-staging || true
    - echo "🛑 Staging environment stopped"
  environment:
    name: staging
    action: stop
  when: manual
  only:
    - main

stop:production:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker stop ${APP_NAME}-production || true
    - docker rm ${APP_NAME}-production || true
    - echo "🛑 Production environment stopped"
  environment:
    name: production
    action: stop
  when: manual
  only:
    - tags
```

**Aspectos clave del pipeline:**

1. **Sin variables sensibles hardcodeadas:** Todo viene de GitLab Variables
2. **Templates reutilizables:** `.build_template`, `.test_template`, `.deploy_template`
3. **Environments explícitos:** `development`, `staging`, `production`
4. **Deployment manual:** `when: manual` para control explícito
5. **Stop jobs:** Permite limpiar environments desde GitLab UI
6. **Branch-based deployment:**
   - `develop` → development
   - `main` → staging
   - `tags` → production

### Paso 3.2: Commit y push

```bash
cd ~/formacion-cd/app-config-gitlab
git add .gitlab-ci.yml
git commit -m "Add CI/CD pipeline with environments"
git push origin main
```

### Paso 3.3: Crear rama develop

```bash
git checkout -b develop
git push -u origin develop
```

### ✓ Checkpoint 3: Pipeline configurado

---

## PARTE 4: Ejecutar Deployments (10 min)

### Paso 4.1: Deploy a Development

1. Cambiar a rama `develop` en GitLab
2. Navegar: **CI/CD > Pipelines**
3. Debería haber un pipeline corriendo
4. Esperar a que complete stages `build` y `test`
5. En stage `deploy`, click en botón "play" (▶️) de `deploy:development`
6. Esperar completitud
7. Ver logs en el job

**Logs esperados:**

```
🚀 Deploying to development...
⏳ Esperando inicio...
📋 Logs del contenedor:
============================================================
🚀 Iniciando aplicación
============================================================

📋 Configuración actual:
{
  "environment": "development",
  "database": {
    "host": "localhost",
    "port": 5432,
    "password": "***"
  },
  "application": {
    "log_level": "DEBUG",
    "cache_enabled": false
  },
  ...
}

✅ Aplicación ejecutada exitosamente en: development
```

### Paso 4.2: Verificar Environment en GitLab

1. Navegar: **Deployments > Environments**
2. Deberías ver: `development` con estado "Active"
3. Click en environment para ver historial

### Paso 4.3: Deploy a Staging

1. Volver a rama `main`
2. Merge `develop` a `main`:

```bash
git checkout main
git merge develop
git push origin main
```

3. En GitLab: **CI/CD > Pipelines**
4. Click "play" en `deploy:staging`
5. Ver logs - debería mostrar config de staging

### Paso 4.4: Deploy a Production (simulado con tag)

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

1. En GitLab: **CI/CD > Pipelines**
2. Buscar pipeline del tag `v1.0.0`
3. Click "play" en `deploy:production`
4. Ver logs - debería mostrar config de production

**Nota:** Como `DB_PASSWORD` está enmascarado, no aparecerá en logs.

### Paso 4.5: Ver todos los Environments

**Deployments > Environments** debería mostrar:

- ✅ `production` (v1.0.0)
- ✅ `staging` (main)
- ✅ `development` (develop)

Cada uno con su configuración específica.

### ✓ Checkpoint 4: Deployments exitosos en múltiples environments

---

## PARTE 5: Best Practices y Troubleshooting (10 min)

### Best Practices de Configuración en GitLab

#### ✅ DO - Hacer

1. **Usar Environment Scope:**
   ```
   DB_HOST → development = localhost
   DB_HOST → production = prod-db.internal
   ```

2. **Proteger variables sensibles:**
   - Habilitar "Protected" para production
   - Habilitar "Masked" para passwords/tokens

3. **Documentar variables requeridas:**
   - Mantener `.env.example` actualizado
   - Crear archivo `CONFIG.md` con documentación

4. **Validar configuración en app:**
   ```python
   if not os.getenv("DB_PASSWORD"):
       raise ValueError("DB_PASSWORD no configurado")
   ```

5. **Usar valores por defecto seguros:**
   ```python
   LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # No DEBUG por defecto
   ```

6. **GitLab Environments para tracking:**
   - Un environment por entorno (dev, staging, prod)
   - Usar `on_stop` para cleanup

7. **Separar ramas por environment:**
   - `develop` → development
   - `main` → staging
   - `tags` → production

#### ❌ DON'T - No hacer

1. **Hardcodear secretos en .gitlab-ci.yml:**
   ```yaml
   # ❌ NUNCA
   variables:
     DB_PASSWORD: "supersecret123"
   ```

2. **Commitear archivos .env:**
   ```bash
   # ❌ Asegurar que .env está en .gitignore
   ```

3. **Usar mismas credenciales en todos los ambientes:**
   ```
   # ❌ Dev y prod con mismo DB_PASSWORD
   ```

4. **Exponer secretos en logs:**
   ```bash
   # ❌ NUNCA
   echo "Password: ${DB_PASSWORD}"
   ```

5. **Variables protegidas sin proteger la rama:**
   ```
   # ❌ Variable protegida pero rama sin proteger
   ```

### Troubleshooting

#### ❌ Error: "DB_PASSWORD no está configurado"

**Causa:** Variable no definida para el environment específico.

**Solución:**
1. Verificar que la variable existe en GitLab
2. Verificar que "Environment scope" coincide con el environment del job
3. Verificar que la rama está protegida (si la variable es Protected)

#### ❌ Error: Variable muestra valor de otro environment

**Causa:** Environment scope mal configurado.

**Solución:**
1. Ir a **Settings > CI/CD > Variables**
2. Verificar que cada variable tiene el scope correcto:
   - `DB_HOST` con scope `development` debe ser diferente de
   - `DB_HOST` con scope `production`

#### ❌ Error: "This job is stuck because you don't have any active runners"

**Causa:** No hay runners disponibles o con tags correctos.

**Solución:**
1. Eliminar `tags:` del job si usas shared runners
2. O configurar un runner con el tag especificado

#### ❌ Warning: Variable no está enmascarada en logs

**Causa:** Variable contiene secreto pero no está marcada como "Masked".

**Solución:**
1. Editar variable en GitLab
2. Marcar checkbox "Mask variable"
3. Re-ejecutar pipeline

#### ❌ Deploy funciona en staging pero falla en production

**Causa:** Variables protegidas no disponibles en rama/tag no protegido.

**Solución:**
1. Verificar que main/tags están protegidos en **Settings > Repository**
2. Verificar que variables tienen "Protected" habilitado

### Verificar Variables Disponibles en Job

Agregar temporalmente a un job:

```yaml
script:
  - echo "=== Variables disponibles ==="
  - env | grep -E "APP_|DB_|LOG_|FEATURE_" | sort
  - echo "=== Environment ==="
  - echo "CI_ENVIRONMENT_NAME: ${CI_ENVIRONMENT_NAME}"
  - echo "CI_ENVIRONMENT_SLUG: ${CI_ENVIRONMENT_SLUG}"
```

**Nota:** Remover después - no exponer secretos en logs.

---

## Validación Final

**Checklist:**

- [ ] `app.py` lee configuración desde variables de entorno
- [ ] Validación de variables críticas implementada
- [ ] `.env.example` y `CONFIG.md` documentan todas las variables
- [ ] `.gitignore` excluye archivos `.env`
- [ ] Variables configuradas en GitLab para 3 environments
- [ ] Variables sensibles marcadas como "Masked"
- [ ] Variables de producción marcadas como "Protected"
- [ ] Rama `main` está protegida
- [ ] Pipeline usa templates para reutilización
- [ ] Pipeline no contiene secretos hardcodeados
- [ ] Deployment a development ejecutado exitosamente
- [ ] Deployment a staging ejecutado exitosamente
- [ ] Deployment a production ejecutado exitosamente
- [ ] Environments visibles en **Deployments > Environments**
- [ ] Configuración diferente en cada environment validada en logs
- [ ] `docker logs` muestra configuración correcta para cada ambiente

---

## Conceptos Finales

### Principio 12-Factor App

Esta práctica implementa el **Factor III: Configuration** de la metodología 12-factor:

> "Store config in the environment"

**Separación correcta:**
- **Código:** Lógica de negocio, inmutable entre ambientes
- **Configuración:** Variables que cambian por ambiente, inyectadas en runtime
- **Secretos:** Credenciales manejadas por CI/CD system, nunca en código

### Ventajas de este Approach

1. **Seguridad:**
   - Secretos nunca en código
   - Variables enmascaradas en logs
   - Acceso controlado por protected branches

2. **Escalabilidad:**
   - Mismo código corre en N ambientes
   - Agregar nuevo ambiente = agregar variables
   - Sin rebuilds por cambio de config

3. **Auditabilidad:**
   - GitLab registra quién cambió qué variable
   - Deployment history por environment
   - Trazabilidad completa

4. **Simplicidad Operacional:**
   - Developers no necesitan acceso a secretos de producción
   - CI/CD automatiza inyección de config
   - Rollback de config independiente de código

### Architecture Pattern

```
┌─────────────────────────────────────────────────────┐
│                   GitLab Variables                   │
│  (Settings > CI/CD > Variables)                     │
│                                                      │
│  development:                                        │
│    DB_HOST=localhost                                │
│    LOG_LEVEL=DEBUG                                  │
│                                                      │
│  staging:                                           │
│    DB_HOST=staging-db                               │
│    LOG_LEVEL=INFO                                   │
│                                                      │
│  production:                                        │
│    DB_HOST=prod-db (protected, masked)             │
│    LOG_LEVEL=ERROR                                  │
└─────────────────────────────────────────────────────┘
                        │
                        │ Runtime injection
                        ▼
┌─────────────────────────────────────────────────────┐
│              Docker Container                        │
│                                                      │
│  app.py (same code)                                 │
│    ├─ reads: os.getenv("DB_HOST")                  │
│    ├─ reads: os.getenv("LOG_LEVEL")                │
│    └─ adapts behavior per environment               │
└─────────────────────────────────────────────────────┘
```

**Resultado:** Una imagen Docker, múltiples configuraciones, comportamiento adaptativo.

Esta es la forma profesional y segura de gestionar configuración en CI/CD moderno.
