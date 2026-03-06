# Módulo 4 — Teoría: Herramientas CI/CD (Jenkins y GitLab CI/CD)

## Objetivo del módulo

En este módulo vas a aprender cómo funcionan Jenkins y GitLab CI/CD como herramientas de automatización. El foco está en entender su arquitectura, su lenguaje básico de pipeline y cómo ejecutar procesos simples de `build` y `test` de manera repetible.

Este módulo no entra aún en pipelines completas de despliegue a producción: esa parte se trabaja en el Módulo 5.

---

## Qué debes saber al terminar

Al finalizar este contenido deberías poder:

1. Explicar qué problema resuelven Jenkins y GitLab CI/CD.
2. Diferenciar un job freestyle de una pipeline as code.
3. Leer una pipeline básica en `Jenkinsfile` y en `.gitlab-ci.yml`.
4. Entender qué son runners/agentes y por qué son necesarios.
5. Identificar errores frecuentes en ejecución revisando logs.

---

## 4.1 Jenkins

### 4.1.1 ¿Qué es Jenkins?

Jenkins es un servidor de automatización. Su función principal es ejecutar tareas técnicas de forma consistente cada vez que hay cambios en el código.

Ejemplos de tareas típicas:

- descargar código desde Git,
- instalar dependencias,
- lanzar tests,
- generar artefactos,
- publicar resultados.

Si una tarea siempre debe hacerse igual, Jenkins ayuda a que no dependa de “quién la ejecuta”, sino de una definición común y versionada.

### 4.1.2 ¿Por qué Jenkins en proyectos de datos?

En Big Data es normal combinar Python, Java, Spark, conectores de base de datos y herramientas de calidad. Ese entorno mixto genera fricción cuando todo se hace manualmente.

Jenkins aporta:

- estandarización de procesos,
- repetibilidad de ejecuciones,
- trazabilidad por build,
- integración con herramientas externas mediante plugins.

La idea clave es simple: **Jenkins transforma tareas manuales en un flujo automatizado y auditable**.

### 4.1.3 Arquitectura básica

Componentes esenciales:

- **Controller:** gestiona configuración, cola de ejecuciones y estado de jobs.
- **Agents:** nodos donde se ejecutan realmente los jobs.
- **Jobs/Pipelines:** definición de lo que se va a ejecutar.
- **Plugins:** extensiones para conectar Jenkins con Git, credenciales, notificaciones, etc.

En laboratorios pequeños, controller y ejecución pueden ir juntos. En entornos más serios, separar agentes mejora escalabilidad, seguridad y aislamiento.

### 4.1.4 Jobs freestyle vs pipelines

#### Job freestyle

- Se configura desde interfaz gráfica.
- Es rápido para aprender los primeros pasos.
- Escala peor cuando el flujo crece.

#### Pipeline (Pipeline as Code)

- Se define en un archivo `Jenkinsfile`.
- Se guarda en Git junto con el proyecto.
- Permite revisión de cambios, control de versiones y mayor mantenibilidad.

En el mundo profesional, la práctica recomendada es usar pipeline as code.

### 4.1.5 Jenkinsfile declarativo: estructura mínima

Un Jenkinsfile declarativo suele incluir:

- `pipeline` (bloque principal),
- `agent` (dónde se ejecuta),
- `stages` (fases),
- `steps` (comandos de cada fase),
- `post` (acciones finales).

Ejemplo básico:

```groovy
pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        echo 'Construcción básica del proyecto'
      }
    }

    stage('Test') {
      steps {
        sh 'python -m pytest -q || true'
      }
    }
  }

  post {
    always {
      echo 'Pipeline finalizada'
    }
  }
}
```

Cómo leer este archivo:

1. Jenkins reserva un agente (`agent any`).
2. Ejecuta primero la fase `Build`.
3. Luego ejecuta la fase `Test`.
4. Pase lo que pase, entra en `post` y deja mensaje de cierre.

### 4.1.6 Plugins esenciales

Un conjunto inicial razonable:

- **Git plugin:** permite integración con repositorios.
- **Pipeline plugin suite:** soporte completo para `Jenkinsfile`.
- **Credentials Binding:** inyección segura de credenciales.
- **Blue Ocean** (opcional): visualización más amigable.

Buenas prácticas:

- instalar solo lo necesario,
- mantener plugins actualizados,
- evitar acumulación de plugins sin uso.

### 4.1.7 Triggers de ejecución

Un trigger es el evento que provoca que Jenkins lance una pipeline. Entender triggers es crucial porque determinan cuándo y por qué se ejecuta tu automatización.

#### Tipos de triggers

**1. Manual**

- Jenkins no hace nada automáticamente.
- Tú decides cuándo ejecutar presionando botón "Build Now".
- Útil para primeros pasos, debugging y ejecuciones puntuales.

**2. Webhook (recomendado para empezar)**

- Git (GitHub, GitLab, etc.) notifica a Jenkins cada vez que hay un push o merge.
- Jenkins recibe evento HTTP y lanza la pipeline inmediatamente.
- Ventaja: casi instantáneo, responde a cambios reales.
- Desventaja: requiere configuración de webhooks.

Ejemplo de flujo:

```
1. Haces push a rama main
2. Git envía webhook a Jenkins
3. Jenkins detecta cambio
4. Jenkins clona código y ejecuta pipeline
```

**3. Poll SCM (sondeo periódico)**

- Jenkins comprueba repositorio cada X minutos ("¿hay cambios?").
- Si hay cambios, ejecuta pipeline.
- Ventaja: simple, sin configuración de webhooks.
- Desventaja: latencia (espera a siguiente sondeo) y consume recursos.

Ejemplo de configuración: "cada 5 minutos".

**4. Programado (cron)**

- Pipeline se ejecuta en horario fijo sin depender de cambios de código.
- Útil para procesos de datos periódicos (ETL nocturnos, validaciones diarias).

Ejemplo: "ejecutar cada día a las 02:00 AM".

#### ¿Cuándo usar cada uno?

- **Manual:** desarrollo local, testing, primeros pasos.
- **Webhook:** desarrollo en equipo, integración continua real-time.
- **Poll SCM:** equipos sin acceso a webhooks, sistemas legados.
- **Cron:** pipelines de batch, mantenimiento programado.

#### Combinación recomendada para formación inicial

Manual + webhook es la mejor pareja para aprender:

- Manual te permite lanzar a voluntad (sin esperar evento).
- Webhook te enseña cómo reacciona Jenkins ante cambios reales.

Con ambos juntos, entiendes causa-efecto sin complicación extra.

### 4.1.8 Logs y diagnóstico en Jenkins

Cada ejecución genera logs por build. Aprender a leerlos te ahorra mucho tiempo.

Checklist mínimo de troubleshooting:

1. Identifica la build exacta que falló.
2. Localiza la stage con error.
3. Revisa el comando que falla y su salida.
4. Comprueba si el problema es de código, dependencias o credenciales.

---

## 4.2 GitLab CI/CD

### 4.2.1 ¿Qué es GitLab CI/CD?

GitLab CI/CD es el sistema de automatización integrado en GitLab. La ventaja principal es que repositorio, merge requests y pipelines están en la misma plataforma.

Esto mejora la trazabilidad porque cada pipeline queda asociada a un commit o merge request concreto.

### 4.2.2 Conceptos fundamentales

- **Stage:** fase lógica de la pipeline (`build`, `test`, `deploy`).
- **Job:** tarea concreta dentro de una stage.
- **Script:** comandos que ejecuta el job.

Regla básica de ejecución:

- jobs de la misma stage pueden ir en paralelo,
- la siguiente stage espera a la anterior.

### 4.2.3 Archivo `.gitlab-ci.yml`

Toda la pipeline se define en este archivo dentro del repositorio.

Ejemplo mínimo:

```yaml
stages:
  - build
  - test

build_job:
  stage: build
  script:
    - echo "Construyendo proyecto"

test_job:
  stage: test
  script:
    - echo "Ejecutando tests"
```

Cómo leerlo:

1. GitLab crea dos etapas: `build` y `test`.
2. Ejecuta `build_job`.
3. Si termina correctamente, ejecuta `test_job`.

### 4.2.4 Runners y executors

GitLab Runner es el componente que ejecuta jobs.

- **Runner:** servicio que toma jobs de GitLab.
- **Executor:** modo de ejecución del runner (por ejemplo, `shell` o `docker`).

En entornos formativos y de equipos iniciales, `docker` suele ser preferible porque aísla dependencias y mejora reproducibilidad.

### 4.2.5 Variables y artifacts

#### Variables

Sirven para parametrizar la pipeline sin hardcodear datos sensibles o específicos de entorno.

Ejemplos:

- host de base de datos,
- token de autenticación,
- nombre de entorno (`dev`, `test`, `prod`).

Buenas prácticas:

- no guardar secretos en el `.gitlab-ci.yml`,
- usar variables protegidas/masked en GitLab.

#### Artifacts

Artifacts son archivos que un job guarda para etapas posteriores o para inspección.

Ejemplos comunes:

- reportes de test,
- resultados de validación,
- paquetes generados.

Sin artifacts, muchas veces los resultados de una etapa se pierden al terminar el job.

### 4.2.6 Logs y troubleshooting en GitLab

En cada job puedes abrir la consola de ejecución.

Checklist rápido:

1. Verifica en qué stage falla.
2. Lee el último comando ejecutado antes del error.
3. Comprueba si faltan dependencias o variables.
4. Reintenta solo tras corregir causa raíz.

---

## Jenkins vs GitLab CI/CD (comparativa inicial)

| Criterio | Jenkins | GitLab CI/CD |
|---|---|---|
| Enfoque | Motor de automatización muy flexible | CI/CD integrada en GitLab |
| Arranque inicial | Requiere instalación y plugins | Rápido si ya trabajas en GitLab |
| Definición pipeline | `Jenkinsfile` | `.gitlab-ci.yml` |
| Integraciones | Muy amplio ecosistema de plugins | Integración nativa con MR/repos |
| Curva inicial | Media | Media-baja |

Conclusión práctica: no existe herramienta universalmente mejor. La elección depende del contexto técnico y organizativo.

---

## Errores frecuentes al empezar (y cómo evitarlos)

1. **Confundir CI y CD**  
   CI valida integración continua; CD automatiza entrega/despliegue en distintos grados.

2. **Pensar que la herramienta diseña sola una pipeline correcta**  
   Jenkins/GitLab ejecutan lo que defines; si el diseño es pobre, el resultado también.

3. **No versionar la pipeline**  
   `Jenkinsfile` y `.gitlab-ci.yml` deben vivir en Git para trazabilidad.

4. **Guardar secretos en texto plano**  
   Usa gestores de credenciales y variables seguras.

5. **No revisar logs con método**  
   La mayoría de fallos se resuelve leyendo bien salida y contexto del job.

---

## Resumen final

Jenkins y GitLab CI/CD son dos formas sólidas de automatizar integración y entrega continua. En este módulo la clave es comprender su funcionamiento base: estructura de pipeline, ejecución por etapas, rol de runners/agentes y lectura de logs.

Con esta base, el siguiente paso natural es diseñar pipelines completas con empaquetado, despliegue y gestión de entornos, que se desarrolla en el Módulo 5.
