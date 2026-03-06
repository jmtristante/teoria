# Ejemplo 01 — Docker básico con Python

## Objetivo
Construir una imagen simple, ejecutar un contenedor y guardar un CSV en un volumen para capturas de pantalla.

## Comandos
```powershell
cd ejemplos-modulo-3/01-python-basico

docker build -t curso-bigdata/python-transform:1.0.0 .
docker run --rm curso-bigdata/python-transform:1.0.0
```

## Ejecución con volumen (recomendado)
```powershell
docker run --rm -v ${PWD}/salida:/data curso-bigdata/python-transform:1.0.0
```

Después de ejecutar, el archivo `salida/ventas_transformadas.csv` quedará en tu máquina.
