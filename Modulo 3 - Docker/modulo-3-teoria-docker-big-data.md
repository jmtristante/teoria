# Módulo 3 — Teoría: Docker para Big Data

## Guía docente

### Objetivo general del módulo
Comprender cómo Docker aporta **reproducibilidad, portabilidad y estandarización** en proyectos de datos, y cómo se integra en una estrategia de CI/CD para construir, distribuir y desplegar aplicaciones de Big Data de forma consistente.

### Resultados de aprendizaje esperados
Al finalizar la parte teórica, el alumnado será capaz de:

1. Explicar la diferencia entre imagen, contenedor y Dockerfile.
2. Argumentar por qué Docker es especialmente útil en entornos Big Data.
3. Diseñar una estrategia básica para dockerizar aplicaciones PySpark.
4. Entender cómo funciona Docker Compose en arquitecturas multi-servicio.
5. Aplicar criterios de versionado y publicación de imágenes en un registry.
6. Identificar riesgos habituales (seguridad, tamaño, compatibilidad de versiones) y mitigarlos.

---

## 3.1 Fundamentos de Docker

### 3.1.1 ¿Qué son los contenedores?
Un contenedor es una unidad ligera y aislada que empaqueta una aplicación con sus dependencias necesarias para ejecutarse. A diferencia de la virtualización tradicional, no necesita incluir un sistema operativo completo por cada instancia.

En términos prácticos, esto significa que si una aplicación funciona en el contenedor del entorno de desarrollo, debería comportarse del mismo modo en integración, preproducción o producción, siempre que se mantengan las mismas versiones de imagen y configuración.

Para personas que empiezan desde cero, una analogía útil es:

- **Imagen Docker** = receta de cocina.
- **Contenedor** = plato ya cocinado usando esa receta.

Con la misma receta, el plato debería salir siempre igual. Ese es precisamente el valor de Docker: repetir ejecuciones con menos sorpresas.

### 3.1.2 Diferencia entre máquina virtual y contenedor
Aunque ambos conceptos buscan aislamiento, sus modelos son distintos:

- **Máquina virtual (VM):** virtualiza hardware y ejecuta un sistema operativo completo por cada VM.
- **Contenedor:** virtualiza a nivel de sistema operativo, compartiendo kernel con el host.

Implicaciones directas:

- Menor consumo de recursos en contenedores.
- Menor tiempo de arranque.
- Mayor densidad de despliegue por nodo.
- Ciclos de build-test-run más rápidos.

En escenarios Big Data, donde hay procesos distribuidos y múltiples componentes (procesamiento, almacenamiento, orquestación), esta ligereza es clave para iterar más rápido.

### 3.1.3 Conceptos base de Docker

#### Imagen
Una imagen Docker es una plantilla inmutable que contiene:

- Sistema base (por ejemplo, Debian slim o Alpine).
- Runtime (Python, Java, etc.).
- Dependencias de aplicación.
- Código y configuración por defecto.

Una imagen no “se ejecuta” por sí misma; se usa para crear contenedores.

Importante para principiantes: cuando cambias código en tu proyecto, normalmente debes **reconstruir la imagen** para que esos cambios se reflejen dentro del contenedor.

#### Contenedor
Es la instancia en ejecución de una imagen. Puede leerse como “imagen + estado en tiempo de ejecución”.

Un contenedor puede pararse, arrancarse y eliminarse. Si no hay volúmenes, los datos escritos dentro del contenedor suelen perderse al eliminarlo.

#### Dockerfile
Archivo declarativo donde se define cómo construir una imagen. Incluye instrucciones como:

- `FROM` (imagen base)
- `WORKDIR` (directorio de trabajo)
- `COPY` (copiar código)
- `RUN` (instalaciones/comandos)
- `CMD` o `ENTRYPOINT` (comando de inicio)

Piensa en el Dockerfile como un historial de pasos automáticos: en lugar de “instalar cosas a mano”, describes esos pasos una vez y Docker los repite siempre igual.

#### Volúmenes
Mecanismo para persistir datos fuera del ciclo de vida del contenedor. Muy importante en datos cuando se requiere:

- Mantener outputs entre ejecuciones.
- Compartir datasets entre servicios.
- Evitar pérdida de información al recrear contenedores.

#### Red (networking)
Permite comunicación entre contenedores. En Compose, los servicios comparten una red virtual donde se resuelven por nombre de servicio (por ejemplo, `postgres` o `spark-master`).

### 3.1.4 Ciclo de vida básico
Flujo habitual:

1. Definir Dockerfile.
2. Construir imagen (`docker build`).
3. Ejecutar contenedor (`docker run`).
4. Observar estado y logs (`docker ps`, `docker logs`).
5. Parar o eliminar contenedor (`docker stop`, `docker rm`).

Desde una perspectiva docente, es importante enfatizar que en Docker se opera de forma **declarativa y repetible**: una vez definido el build, se puede reproducir tantas veces como sea necesario con resultados previsibles.

Lectura rápida de los comandos para alumnado sin experiencia:

- `docker build`: "crea una imagen" a partir del Dockerfile.
- `docker run`: "lanza un contenedor" con esa imagen.
- `docker ps`: "lista contenedores en ejecución".
- `docker logs`: "muestra lo que la app imprime".
- `docker stop`: "detiene" un contenedor.
- `docker rm`: "elimina" un contenedor detenido.

Consejo práctico: en formación inicial, pedir siempre al alumnado que siga la secuencia `build -> run -> ps -> logs` ayuda a crear hábito operativo.

### 3.1.5 Buenas prácticas de Dockerfile

#### Selección de imagen base
Elegir imágenes pequeñas y mantenidas reduce superficie de ataque y tiempo de descarga. En Python suele recomendarse `python:X.Y-slim` frente a variantes completas, salvo necesidad explícita.

#### Optimización de capas
Cada instrucción crea una capa. Conviene:

- Unir comandos relacionados en un solo `RUN`.
- Copiar primero archivos de dependencias para aprovechar caché.
- Evitar invalidar capas innecesariamente.

Ejemplo mental sencillo: si instalas dependencias antes de copiar todo el código, Docker puede reutilizar capas y el siguiente build será mucho más rápido.

#### Uso de `.dockerignore`
Evita copiar al contexto de build archivos no necesarios (`.git`, caches, notebooks pesados, datasets locales, etc.), reduciendo tiempos y tamaño.

#### Principio de mínimo privilegio
Siempre que sea posible, ejecutar con usuario no root. Mejora seguridad y reduce impacto en caso de vulnerabilidad.

#### Inmutabilidad y trazabilidad
No modificar contenedores manualmente en producción. La práctica correcta es:

- Cambiar código o Dockerfile.
- Rebuild de imagen.
- Redeploy.

Este punto es clave en CI/CD: el entorno no depende de "lo que alguien tocó por consola", sino de artefactos versionados.

#### Multi-stage builds
Especialmente útil cuando hay fase de compilación. Permite separar entorno de build del entorno final de runtime y generar imágenes más ligeras.

### 3.1.6 Valor específico en Big Data
En proyectos de datos aparecen frecuentemente estos problemas:

- Dependencias complejas (Python, Java, librerías nativas).
- Diferencias entre equipos (SO, versiones, paths).
- Inconsistencias entre desarrollo y producción.

Docker mitiga estos puntos al encapsular el entorno. Esto es muy relevante para pipelines ETL y jobs PySpark, donde pequeños desajustes de versión pueden provocar fallos difíciles de diagnosticar.

---

## 3.2 Docker para aplicaciones Big Data

### 3.2.1 Dockerizar una aplicación de datos: enfoque práctico
Una aplicación Big Data suele componerse de más de un servicio. Por ejemplo:

- Servicio de procesamiento (Python/PySpark).
- Base de datos destino (PostgreSQL).
- Motor de orquestación (Airflow) o scheduler.
- Sistemas de mensajería/almacenamiento (según caso).

Docker permite empaquetar cada bloque y ejecutarlos con configuración controlada.

### 3.2.2 Particularidades de PySpark
Dockerizar PySpark exige prestar atención a compatibilidad entre:

- Versión de Spark.
- Versión de Java.
- Versión de Python.
- Dependencias adicionales (drivers JDBC, librerías de conectividad, etc.).

En formación, conviene destacar una regla práctica: **fijar versiones explícitas** y evitar depender de “latest” para componentes críticos.

### 3.2.3 Docker Compose para múltiples servicios
`docker-compose.yml` define y coordina varios contenedores como una única aplicación lógica.

Beneficios didácticos y operativos:

- Arranque integral con un único comando.
- Definición declarativa de servicios y relaciones.
- Red compartida y resolución por nombre.
- Gestión centralizada de variables y puertos.

Elementos típicos en Compose:

- `services`: lista de servicios.
- `build` o `image`: origen del contenedor.
- `ports`: mapeo host-contenedor.
- `volumes`: persistencia/compartición.
- `environment`: configuración por entorno.
- `depends_on`: orden de arranque lógico.
- `healthcheck`: verificación de disponibilidad.

Para principiantes, el salto conceptual importante es este: con un único `docker compose up` puedes levantar un "mini-entorno" completo (por ejemplo app + base de datos) sin instalar cada componente por separado en tu sistema.

También conviene remarcar que `depends_on` ayuda con el orden de arranque, pero no siempre garantiza que una aplicación ya esté 100% lista para recibir conexiones. Por eso combinarlo con `healthcheck` y/o reintentos en la aplicación es una práctica sólida.

### 3.2.4 Patrón de arquitectura local para Big Data
Para prácticas formativas, una arquitectura mínima reproducible puede ser:

- Un servicio `app` con el job Python/PySpark.
- Un servicio `postgres` como almacenamiento.
- (Opcional) un servicio `spark` o `airflow` para ampliar la práctica.

Objetivo pedagógico: demostrar integración de componentes y trazabilidad del pipeline, no replicar toda la complejidad de producción.

### 3.2.5 Configuración y variables de entorno
En datos, muchos parámetros cambian según entorno:

- Hosts y puertos.
- Credenciales.
- Rutas de entrada/salida.
- Nivel de logging.

Docker y Compose permiten externalizar configuración mediante variables de entorno y archivos `.env`, facilitando despliegues consistentes entre `dev`, `test` y `prod`.

Regla de oro para alumnado inicial: **el código no debería cambiar entre entornos; lo que cambia es la configuración**.

### 3.2.6 Gestión de datos y volúmenes
En aplicaciones Big Data es fundamental decidir qué datos:

- Son temporales (cache/intermedios).
- Deben persistir (outputs, checkpoints, metadatos).

Los volúmenes proporcionan persistencia desacoplada del contenedor. Sin este patrón, recrear contenedores implicaría pérdida de información.

Mensaje pedagógico útil: "contenedor efímero, datos persistentes". Entender esta idea evita muchos errores al principio.

### 3.2.7 Observabilidad básica en contenedores
Antes de hablar de herramientas avanzadas, un nivel inicial incluye:

- Logs por contenedor.
- Estado de servicios.
- Health checks simples.

En el contexto de CI/CD, estas señales permiten decidir si una etapa pasa o falla.

### 3.2.8 Errores comunes al dockerizar Big Data

1. **Imágenes demasiado grandes:** builds lentos y despliegues costosos.
2. **Versiones no fijadas:** comportamientos no deterministas.
3. **Datos metidos en la imagen:** acoplamiento y baja flexibilidad.
4. **Credenciales hardcodeadas:** riesgo de seguridad alto.
5. **Ausencia de health checks:** difícil detectar servicios caídos.
6. **Confundir entorno local con producción:** diferencias de red, recursos y seguridad.

### 3.2.9 Criterios de calidad para una dockerización correcta
Una solución bien planteada debería cumplir:

- Repetibilidad (mismo resultado al reconstruir).
- Portabilidad (funciona en distintos hosts compatibles).
- Trazabilidad (imagen identificable por versión/commit).
- Mantenibilidad (estructura clara de Dockerfile y Compose).
- Seguridad base (mínimo privilegio, dependencias controladas).

---

## 3.3 Registro de imágenes Docker

### 3.3.1 ¿Qué es un Docker Registry?
Es un repositorio central de imágenes donde los equipos publican y consumen versiones de aplicaciones. Puede ser:

- Público (por ejemplo, repositorios abiertos).
- Privado (infraestructura interna o servicio gestionado).

En CI/CD, el registry es el punto de unión entre build y deploy: la pipeline construye una imagen y la publica; los entornos despliegan esa imagen exacta.

### 3.3.2 Operaciones fundamentales

- **Tag:** asignar identificador versionado a una imagen.
- **Push:** subir imagen al registry.
- **Pull:** descargar imagen desde registry.

Estas operaciones no son meramente técnicas; son parte del control de versiones operativo.

Interpretación práctica:

- Si no haces `push`, tu imagen solo existe en tu máquina.
- Si un compañero hace `pull` del mismo tag, ambos ejecutan el mismo artefacto.
- Esto reduce diferencias entre equipos y acelera soporte técnico.

### 3.3.3 Estrategias de versionado y tagging
Una estrategia robusta combina distintos tipos de tag:

- **Semántico** (`v1.4.2`): comunica evolución funcional.
- **Inmutable por commit** (hash corto): garantiza trazabilidad exacta.
- **Canal/entorno** (`dev`, `staging`, `prod`): facilita promoción entre etapas.

Buenas prácticas clave:

1. Tratar los tags de versión como inmutables.
2. Evitar dependencia exclusiva de `latest`.
3. Publicar convención de nombres para todo el equipo.

### 3.3.4 Trazabilidad extremo a extremo
En una organización madura, debe poder responderse rápidamente:

- ¿Qué imagen está en producción?
- ¿Qué commit la generó?
- ¿Qué tests pasaron antes de publicarla?
- ¿Qué cambios incluye respecto a la versión anterior?

Esta capacidad es esencial para auditoría, diagnóstico y rollback.

En clases introductorias merece la pena insistir en la relación entre trazabilidad y confianza: cuando hay incidencia, no se "adivina" qué versión está desplegada; se sabe con exactitud.

### 3.3.5 Seguridad en el registry
Aspectos mínimos que deben enseñarse:

- Control de acceso por roles.
- Escaneo de vulnerabilidades de imágenes.
- Firma/verificación de artefactos (cuando aplique).
- Políticas de retención para eliminar versiones obsoletas.

En Big Data, donde pueden existir datos sensibles y cadenas de procesamiento críticas, la seguridad del artefacto desplegable no es opcional.

### 3.3.6 Políticas de retención y limpieza
Sin gobernanza, los registries crecen de forma descontrolada. Se recomienda:

- Mantener versiones activas y últimas N estables.
- Eliminar imágenes huérfanas o no referenciadas.
- Definir ventanas de retención por entorno/proyecto.

Resultado esperado: menor coste de almacenamiento y mayor claridad operativa.

### 3.3.7 Integración con CI/CD
Flujo típico integrado:

1. Pipeline detecta cambio en repositorio.
2. Ejecuta tests y validaciones.
3. Construye imagen Docker.
4. Etiqueta con versión y commit.
5. Publica en registry.
6. Despliega en entorno objetivo.

Ventaja principal: el despliegue consume artefactos versionados y reproducibles, no código “en crudo”.

Para alumnado novel, este punto puede resumirse así: CI/CD no despliega "tu carpeta del portátil"; despliega una imagen construida, testada y etiquetada.

---

## Anexo práctico: ejemplos ejecutables para clase y capturas

Este anexo complementa la teoría con ejemplos que puedes ejecutar en tu equipo para generar evidencias (capturas de terminal, logs, contenedores y outputs). Todos los ejemplos están pensados para Docker Desktop en Windows con PowerShell.

### Estructura de ejemplos incluida

- `ejemplos-modulo-3/01-python-basico`: Dockerfile simple para script Python de transformación.
- `ejemplos-modulo-3/02-compose-app-postgres`: `docker-compose.yml` con app Python + PostgreSQL.
- `ejemplos-modulo-3/03-compose-spark-postgres`: `docker-compose.yml` con Spark + PostgreSQL.

### Requisitos mínimos previos

1. Docker Desktop instalado y en ejecución.
2. Comando `docker` disponible en terminal.
3. (Recomendado) Tener al menos 6 GB de RAM asignada a Docker Desktop para el ejemplo de Spark.

Comando de verificación inicial:

```powershell
docker version
docker info
```

Si ambos comandos responden sin error, el entorno está listo.

---

### Ejemplo 1 — Docker básico con Python

Objetivo didáctico: reforzar conceptos de **imagen**, **contenedor**, **build** y **volumen**.

Ruta de trabajo:

```powershell
cd ejemplos-modulo-3/01-python-basico
```

Construir imagen:

```powershell
docker build -t curso-bigdata/python-transform:1.0.0 .
```

Ejecutar contenedor (sin volumen):

```powershell
docker run --rm curso-bigdata/python-transform:1.0.0
```

Ejecutar contenedor con volumen para persistir salida:

```powershell
docker run --rm -v ${PWD}/salida:/data curso-bigdata/python-transform:1.0.0
```

Verificar resultado en host:

```powershell
Get-ChildItem .\salida
Get-Content .\salida\ventas_transformadas.csv
```

Capturas recomendadas para dossier formativo:

1. Resultado de `docker build`.
2. Salida del contenedor mostrando dataset transformado.
3. Carpeta `salida` en local con el CSV generado.

---

### Ejemplo 2 — Docker Compose con Python + PostgreSQL

Objetivo didáctico: demostrar arquitectura multi-servicio, red interna, `depends_on` y persistencia con volumen.

Ruta de trabajo:

```powershell
cd ejemplos-modulo-3/02-compose-app-postgres
```

Levantar servicios (build incluido):

```powershell
docker compose up --build
```

Comprobar estado de contenedores:

```powershell
docker ps
```

Validar datos cargados en PostgreSQL:

```powershell
docker exec -it m3_postgres psql -U bigdata -d bigdata -c "SELECT * FROM ventas ORDER BY id;"
```

Apagado de stack:

```powershell
docker compose down
```

Apagado con borrado de volumen (reset completo):

```powershell
docker compose down -v
```

Capturas recomendadas:

1. Logs de `docker compose up --build` hasta mensaje de carga completada.
2. Salida de `docker ps` con ambos servicios arriba.
3. Resultado del `SELECT` con filas insertadas.

---

### Ejemplo 3 — Docker Compose con Spark + PostgreSQL

Objetivo didáctico: mostrar un stack más cercano a Big Data y ejecutar un job PySpark dentro de contenedor.

Ruta de trabajo:

```powershell
cd ejemplos-modulo-3/03-compose-spark-postgres
```

Levantar en segundo plano:

```powershell
docker compose up -d
```

Comprobar servicios:

```powershell
docker ps
```

Ejecutar job PySpark de demostración:

```powershell
docker exec -it m3_spark spark-submit /opt/jobs/job_demo.py
```

Consultar logs del contenedor Spark:

```powershell
docker logs m3_spark --tail 100
```

Apagar stack:

```powershell
docker compose down
```

Capturas recomendadas:

1. `docker ps` con servicios Spark y PostgreSQL activos.
2. UI de Spark en `http://localhost:8080`.
3. Resultado del `spark-submit` mostrando el `df.show()`.

---

### Ejemplo de flujo de tagging y registry local

Objetivo didáctico: enlazar la teoría de registries con una ejecución real de `tag`, `push` y `pull`.

1) Levantar registry local:

```powershell
docker run -d -p 5000:5000 --name local-registry registry:2
```

2) Reusar imagen del ejemplo 1 y etiquetarla para registry local:

```powershell
docker tag curso-bigdata/python-transform:1.0.0 localhost:5000/python-transform:1.0.0
```

3) Publicar imagen en registry local:

```powershell
docker push localhost:5000/python-transform:1.0.0
```

4) Comprobar listado de repositorios:

```powershell
Invoke-RestMethod -Uri http://localhost:5000/v2/_catalog
```

5) Descargar imagen desde registry local:

```powershell
docker pull localhost:5000/python-transform:1.0.0
```

6) Parar y eliminar registry local:

```powershell
docker rm -f local-registry
```

Capturas recomendadas:

1. `docker push` exitoso.
2. Respuesta de `_catalog` con el repositorio publicado.
3. `docker pull` recuperando imagen desde `localhost:5000`.

---

### Sugerencia de narrativa para el aula

Secuencia sugerida en clase para conectar teoría y práctica:

1. Comenzar por ejemplo 1 (imagen y contenedor).
2. Continuar con ejemplo 2 (multi-servicio y persistencia).
3. Cerrar con ejemplo 3 (entorno tipo Big Data).
4. Finalizar con registry (distribución y trazabilidad CI/CD).

Con este orden, el alumnado progresa de conceptos base a arquitectura realista sin saltos bruscos de complejidad.

### Errores típicos de principiante (y cómo corregirlos)

1. **No reconstruir imagen tras cambiar código**  
	Solución: repetir `docker build` y volver a ejecutar el contenedor.

2. **Confundir imagen y contenedor**  
	Solución: recordar "imagen = plantilla" y "contenedor = instancia en ejecución".

3. **Perder datos al borrar contenedores**  
	Solución: usar volúmenes para datos que deban persistir.

4. **Usar siempre `latest` sin versionar**  
	Solución: etiquetar con versión (`v1.0.0`) y, si aplica, con identificador de commit.

5. **Pensar que Docker arregla cualquier problema automáticamente**  
	Solución: mantener buenas prácticas de dependencias, configuración y observabilidad.

---

## Recomendaciones docentes para impartir este módulo

### Enfoque pedagógico sugerido

- Empezar por problema real (“en mi máquina funciona”).
- Introducir Docker como respuesta a reproducibilidad.
- Pasar de conceptos básicos a caso Big Data multi-servicio.
- Cerrar con registry y trazabilidad CI/CD.

### Ideas de mensajes clave durante la clase

1. **Docker no sustituye buenas prácticas; las hace ejecutables y repetibles.**
2. **La imagen es el artefacto central de entrega.**
3. **Compose acelera la colaboración en equipos de datos.**
4. **Sin estrategia de tags y registry, no hay despliegue fiable.**

### Errores conceptuales a corregir en el aula

- “Docker es solo para backend web”: falso, es altamente útil en datos.
- “Con Docker ya no hay problemas de configuración”: se reducen, no desaparecen.
- “`latest` es suficiente”: incorrecto para entornos serios.

---

## Glosario rápido

- **Contenedor:** instancia aislada en ejecución.
- **Imagen:** plantilla inmutable para crear contenedores.
- **Dockerfile:** receta de construcción de imagen.
- **Compose:** definición y ejecución de aplicaciones multi-servicio.
- **Registry:** repositorio de imágenes Docker.
- **Tag:** etiqueta/versionado de imagen.
- **Layer:** capa generada por cada instrucción del build.

---

## Cierre del módulo

El valor de Docker en Big Data no está solo en “empaquetar aplicaciones”, sino en **normalizar cómo se construyen, ejecutan y despliegan pipelines de datos**. Esta normalización permite reducir incidencias por entorno, mejorar la colaboración entre equipos y acelerar la entrega continua.

En términos de CI/CD, Docker transforma el software de datos en un artefacto versionado y portable, listo para pasar por etapas de test, publicación y despliegue con mayor confianza.

Si este marco conceptual queda claro, la parte práctica del módulo (comandos, Dockerfile, Compose y registry) se vuelve natural y mucho más efectiva.
