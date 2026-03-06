# Práctica 3.2 (Guiada) — Docker Compose para aplicación Big Data

## 1) Contexto de la práctica

En esta práctica vas a levantar una arquitectura multi-servicio con Docker Compose. Harás dos bloques:

- **Bloque A:** Python + PostgreSQL (carga de datos real).
- **Bloque B:** Spark + PostgreSQL (stack tipo Big Data + ejecución de job).

- **Duración estimada:** 75–90 minutos
- **Nivel:** Inicial–intermedio

---

## 2) Objetivos de aprendizaje

Al finalizar, deberías poder:

1. Levantar varios servicios con `docker compose up`.
2. Verificar comunicación entre contenedores.
3. Validar persistencia y estado de servicios.
4. Ejecutar un job básico de Spark en contenedor.

---

## 3) Requisitos previos

1. Haber completado la práctica 3.1.
2. Docker Desktop activo.
3. Recursos recomendados para Spark: 6 GB de RAM o más en Docker Desktop.

---

## 4) Bloque A — Compose con Python + PostgreSQL

### Paso A0 — Entrar en carpeta

```powershell
cd ejemplos-modulo-3/02-compose-app-postgres
Get-ChildItem
```

Revisa estructura:

- `docker-compose.yml`
- `app/Dockerfile`
- `app/main.py`
- `app/requirements.txt`

---

### Paso A1 — Analizar `docker-compose.yml`

Antes de ejecutar, identifica:

- servicio `postgres` con variables (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`),
- volumen `pg_data`,
- `healthcheck` de base de datos,
- servicio `app` que depende de `postgres`.

---

### Paso A2 — Levantar stack con build

```powershell
docker compose up --build
```

**Qué observar en logs:**

- PostgreSQL arranca,
- app espera/reintenta conexión si hace falta,
- se crea tabla y se insertan datos,
- mensaje de éxito de carga.

---

### Paso A3 — Verificar contenedores

Abre otra terminal y ejecuta:

```powershell
docker ps
```

Debe aparecer `m3_postgres` y, según el estado, `m3_app_loader` (puede finalizar tras cargar datos).

---

### Paso A4 — Validar datos en PostgreSQL

```powershell
docker exec -it m3_postgres psql -U bigdata -d bigdata -c "SELECT * FROM ventas ORDER BY id;"
```

**Resultado esperado:** filas de ejemplo insertadas.

---

### Paso A5 — Apagar servicios

```powershell
docker compose down
```

Reset completo (borra también volumen):

```powershell
docker compose down -v
```

---

## 5) Bloque B — Compose con Spark + PostgreSQL

### Paso B0 — Entrar en carpeta

```powershell
cd ../03-compose-spark-postgres
Get-ChildItem
```

---

### Paso B1 — Levantar servicios en segundo plano

```powershell
docker compose up -d
```

### Paso B2 — Verificar estado

```powershell
docker ps
```

Deberías ver `m3_spark` y `m3_postgres_spark` en ejecución.

---

### Paso B3 — Abrir UI de Spark

Abre en navegador:

- `http://localhost:8080`

Objetivo: comprobar que el servicio Spark está operativo.

---

### Paso B4 — Ejecutar job PySpark de demostración

```powershell
docker exec -it m3_spark spark-submit /opt/jobs/job_demo.py
```

**Resultado esperado:** salida tabular de `df.show()` con columna transformada.

---

### Paso B5 — Revisar logs de Spark

```powershell
docker logs m3_spark --tail 100
```

---

### Paso B6 — Cerrar stack

```powershell
docker compose down
```

---

## 6) Evidencias a entregar (capturas)

1. `docker compose up --build` del bloque A con carga correcta.
2. Resultado SQL de `SELECT * FROM ventas`.
3. `docker ps` del bloque B con servicios activos.
4. UI de Spark (`localhost:8080`).
5. Salida del `spark-submit`.

---

## 7) Errores frecuentes y solución

1. **Puerto ocupado (`5432` o `8080`)**  
   Cerrar servicio local que use ese puerto o ajustar mapeo en Compose.

2. **Spark tarda en arrancar**  
   Esperar 30–90 segundos y volver a comprobar con `docker ps` / `docker logs`.

3. **No conecta a PostgreSQL**  
   Revisar credenciales y nombre de servicio (`postgres`) en variables de entorno.

4. **Recursos insuficientes**  
   Subir memoria asignada en Docker Desktop.

---

## 8) Criterio de éxito de la práctica

La práctica está completada cuando:

- levantas ambos stacks con Compose,
- verificas datos en PostgreSQL,
- ejecutas un job Spark desde contenedor,
- puedes explicar por qué Compose facilita entornos Big Data reproducibles.
