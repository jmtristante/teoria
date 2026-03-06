# Práctica 3.1 (Guiada) — Fundamentos de Docker

## 1) Contexto de la práctica

En esta práctica vas a construir y ejecutar tu primer contenedor con una app Python sencilla de transformación de datos. El objetivo no es solo “que funcione”, sino entender qué hace cada comando de Docker.

- **Duración estimada:** 45–60 minutos
- **Nivel:** Inicial (sin experiencia previa en Docker)
- **Carpeta de trabajo:** `ejemplos-modulo-3/01-python-basico`

---

## 2) Objetivos de aprendizaje

Al finalizar, deberías poder:

1. Diferenciar imagen y contenedor en un caso real.
2. Construir una imagen desde un `Dockerfile`.
3. Ejecutar contenedores con y sin volumen.
4. Verificar resultados en logs y en archivos de salida.

---

## 3) Requisitos previos

1. Docker Desktop iniciado.
2. Terminal PowerShell abierta en la raíz del proyecto.
3. Tener disponible la carpeta `ejemplos-modulo-3/01-python-basico`.

### Comprobación rápida

```powershell
docker version
docker info
```

**Resultado esperado:** ambos comandos devuelven información sin errores.

---

## 4) Paso a paso

### Paso 0 — Entrar en la carpeta de la práctica

```powershell
cd ejemplos-modulo-3/01-python-basico
Get-ChildItem
```

**Comprueba que existen estos ficheros:**

- `Dockerfile`
- `app.py`
- `requirements.txt`
- `.dockerignore`

---

### Paso 1 — Leer el Dockerfile (entender antes de ejecutar)

Abre el archivo y revisa mentalmente:

- `FROM python:3.11-slim` → imagen base.
- `WORKDIR /app` → directorio de trabajo interno.
- `COPY requirements.txt .` + `RUN pip install ...` → instalación de dependencias.
- `COPY app.py .` → copia de código.
- `CMD ["python", "app.py"]` → comando al arrancar el contenedor.

**Mini chequeo de comprensión:**

- ¿Qué línea define la imagen base?
- ¿Qué línea decide qué se ejecuta al iniciar el contenedor?

---

### Paso 2 — Construir la imagen

```powershell
docker build -t curso-bigdata/python-transform:1.0.0 .
```

**Qué estás haciendo:** creando una imagen versionada (`1.0.0`) a partir del `Dockerfile` actual.

**Resultado esperado:** mensaje final similar a `Successfully tagged curso-bigdata/python-transform:1.0.0`.

Si falla, revisa:

- conexión a internet (descarga de imagen base),
- sintaxis del `Dockerfile`,
- bloqueo de Docker Desktop.

---

### Paso 3 — Ejecutar contenedor (sin volumen)

```powershell
docker run --rm curso-bigdata/python-transform:1.0.0
```

**Qué observar:**

- salida por terminal con dataset original y transformado,
- ruta de salida dentro del contenedor (`/data/...`).

`--rm` hace que el contenedor se elimine automáticamente al terminar.

---

### Paso 4 — Ejecutar con volumen para persistir resultado

```powershell
docker run --rm -v ${PWD}/salida:/data curso-bigdata/python-transform:1.0.0
```

**Qué estás haciendo:** montas una carpeta local (`salida`) dentro del contenedor en la ruta `/data`.

Ahora valida en tu máquina:

```powershell
Get-ChildItem .\salida
Get-Content .\salida\ventas_transformadas.csv
```

**Resultado esperado:** existe `ventas_transformadas.csv` y contiene columna `importe_con_iva`.

---

### Paso 5 — Ver imagen creada

```powershell
docker images | Select-String "curso-bigdata/python-transform"
```

**Resultado esperado:** aparece el tag `1.0.0`.

---

### Paso 6 — (Opcional) Ejecutar contenedor en segundo plano

```powershell
docker run -d --name practica31 curso-bigdata/python-transform:1.0.0 sleep 300
docker ps
docker logs practica31
docker stop practica31
docker rm practica31
```

Objetivo: practicar ciclo de vida de contenedores (`run`, `ps`, `logs`, `stop`, `rm`).

---

## 5) Evidencias a entregar (capturas)

1. `docker build` exitoso.
2. `docker run` mostrando transformación.
3. Carpeta local `salida` con el CSV.
4. (Opcional) `docker ps` y `docker logs` del contenedor en background.

---

## 6) Errores frecuentes y solución

1. **`Cannot connect to the Docker daemon`**  
   Docker Desktop no está iniciado.

2. **No aparece el CSV en `salida`**  
   Revisar que el volumen esté bien escrito: `${PWD}/salida:/data`.

3. **La imagen no se actualiza tras cambiar código**  
   Repetir `docker build ...` antes de `docker run`.

---

## 7) Criterio de éxito de la práctica

La práctica se considera completada cuando:

- construyes una imagen funcional,
- ejecutas el contenedor,
- persistes resultados en host mediante volumen,
- puedes explicar con tus palabras la diferencia entre imagen y contenedor.
