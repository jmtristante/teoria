# Ejemplo 03 — Docker Compose con Spark + PostgreSQL

## Objetivo
Levantar un stack mínimo Big Data con Spark y PostgreSQL para capturas y demostración de arquitectura multi-servicio.

## Levantar servicios
```powershell
cd ejemplos-modulo-3/03-compose-spark-postgres

docker compose up -d
```

UI de Spark: http://localhost:8080

## Ejecutar job de ejemplo dentro del contenedor Spark
```powershell
docker exec -it m3_spark spark-submit /opt/jobs/job_demo.py
```

## Parar servicios
```powershell
docker compose down
```
