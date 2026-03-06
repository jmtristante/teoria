# Práctica 3.3 (Guiada) — Registro de imágenes Docker (Registry)

## 1) Contexto de la práctica

En esta práctica vas a simular un flujo real de publicación y consumo de imágenes usando un registry local. Es una práctica clave para conectar Docker con CI/CD.

- **Duración estimada:** 45–60 minutos
- **Nivel:** Inicial
- **Base utilizada:** imagen generada en práctica 3.1 (`curso-bigdata/python-transform:1.0.0`)

---

## 2) Objetivos de aprendizaje

Al finalizar, deberías poder:

1. Levantar un registry local con Docker.
2. Etiquetar correctamente una imagen para publicarla.
3. Hacer `push` y `pull` de la imagen.
4. Comprobar que el repositorio aparece en el catálogo del registry.

---

## 3) Requisitos previos

1. Docker Desktop en ejecución.
2. Imagen local `curso-bigdata/python-transform:1.0.0` construida.

Verifica imagen local:

```powershell
docker images | Select-String "curso-bigdata/python-transform"
```

Si no existe, vuelve a práctica 3.1 y ejecuta el `docker build`.

---

## 4) Paso a paso

### Paso 0 — Levantar registry local

```powershell
docker run -d -p 5000:5000 --name local-registry registry:2
```

Verifica que está activo:

```powershell
docker ps | Select-String "local-registry"
```

---

### Paso 1 — Etiquetar imagen para registry local

```powershell
docker tag curso-bigdata/python-transform:1.0.0 localhost:5000/python-transform:1.0.0
```

**Qué significa:**

- `localhost:5000` = dirección del registry,
- `python-transform` = nombre del repositorio,
- `1.0.0` = versión.

---

### Paso 2 — Publicar imagen (push)

```powershell
docker push localhost:5000/python-transform:1.0.0
```

**Resultado esperado:** salida con capas subidas y confirmación final.

---

### Paso 3 — Verificar catálogo del registry

```powershell
Invoke-RestMethod -Uri http://localhost:5000/v2/_catalog
```

**Resultado esperado:** JSON con `python-transform` dentro de `repositories`.

---

### Paso 4 — Simular consumo: eliminar tag local y hacer pull

Primero elimina el tag local del registry para obligar descarga:

```powershell
docker rmi localhost:5000/python-transform:1.0.0
```

Ahora vuelve a descargar:

```powershell
docker pull localhost:5000/python-transform:1.0.0
```

Valida que vuelve a aparecer:

```powershell
docker images | Select-String "localhost:5000/python-transform"
```

---

### Paso 5 — Ejecutar imagen descargada desde registry

```powershell
docker run --rm localhost:5000/python-transform:1.0.0
```

Si ves la salida del script, has validado el ciclo completo `push -> pull -> run`.

---

### Paso 6 — Limpieza final

```powershell
docker rm -f local-registry
```

---

## 5) Evidencias a entregar (capturas)

1. Registry local levantado (`docker ps`).
2. `docker push` exitoso.
3. Respuesta del endpoint `_catalog`.
4. `docker pull` exitoso.
5. Ejecución final de la imagen desde `localhost:5000/...`.

---

## 6) Errores frecuentes y solución

1. **Error de conexión a `localhost:5000`**  
   Revisar que `local-registry` esté en ejecución.

2. **`manifest unknown` al hacer pull**  
   Verificar nombre/tag exacto usado en `push`.

3. **Confusión entre imagen original y tag del registry**  
   Comprobar `docker images` y distinguir repositorios.

---

## 7) Criterio de éxito de la práctica

La práctica se considera completada cuando puedes demostrar, con comandos y evidencias, que:

- publicaste una imagen en un registry,
- la recuperaste desde ese registry,
- y ejecutaste exactamente esa versión.

Este flujo es la base de despliegues trazables en CI/CD.
