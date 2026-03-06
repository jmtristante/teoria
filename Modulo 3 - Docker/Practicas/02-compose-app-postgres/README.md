# Ejemplo 02 — Docker Compose con Python + PostgreSQL

## Objetivo
Levantar dos servicios con Compose y cargar datos en PostgreSQL desde un contenedor Python.

## Comandos
```powershell
cd ejemplos-modulo-3/02-compose-app-postgres

docker compose up --build
```

Cuando veas `Carga completada correctamente.`, puedes abrir otra terminal para validar:

```powershell
docker exec -it m3_postgres psql -U bigdata -d bigdata -c "SELECT * FROM ventas ORDER BY id;"
```

## Apagado
```powershell
docker compose down
```

Para eliminar también el volumen:

```powershell
docker compose down -v
```
