# Práctica 4.1 (Guiada) — Jenkins: Instalación y Primera Pipeline

## 1) Contexto de la práctica

En esta práctica vas a instalar Jenkins en Docker, configurar plugins esenciales, crear tu primer job y entender triggers. Es un "hello world" de CI/CD donde verás cómo Jenkins intercepta cambios en código y ejecuta acciones automáticas.

- **Duración estimada:** 90–120 minutos
- **Nivel:** Inicial
- **Requisitos:** Docker Desktop, cuenta en GitHub/GitLab (recomendado)

---

## 2) Objetivos de aprendizaje

Al finalizar deberías poder:

1. Instalar Jenkins en contenedor Docker.
2. Acceder a la interfaz de Jenkins y completar setup inicial.
3. Instalar plugins esenciales para Git y Pipeline.
4. Crear un job freestyle simple.
5. Crear una pipeline declarativa en `Jenkinsfile`.
6. Configurar trigger manual y comprender webhook.

---

## 3) Requisitos previos

1. Docker instalado y en ejecución.
2. Terminal bash/sh abierta (en máquina virtual Linux).
3. (Opcional) acceso a GitHub/GitLab para webhooks.
4. Al menos 2 GB de RAM disponibles para Jenkins.

---

## 4) Paso a paso

### Paso 0 — Levantar Jenkins en Docker

```bash
sudo docker run -d -p 8080:8080 -p 50000:50000 --name jenkins jenkins/jenkins:latest
```

**Qué hace este comando:**

- `-d`: ejecuta en segundo plano.
- `-p 8080:8080`: mapea puerto 8080 (UI).
- `-p 50000:50000`: mapea puerto para agentes.
- `--name jenkins`: nombre del contenedor.

**Verifica que arranque:**

```bash
sudo docker logs jenkins --tail 50
```

Busca línea con `Jenkins initial setup is required`. Cuando veas esa línea, Jenkins está listo (puede tardar 30–60 segundos).

---

### Paso 1 — Acceder a Jenkins

Abre en navegador: `http://localhost:8080`

Verás formulario pidiendo contraseña inicial.

**Obtener contraseña:**

```bash
sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Copia la contraseña (sin saltos de línea) y pégala en Jenkins.

---

### Paso 2 — Setup inicial de Jenkins

1. Pega contraseña.
2. Pantalla siguiente: "Install suggested plugins" (clic).
3. Espera a que termine instalación (puede tardar 2–3 minutos).
4. Crea cuenta de usuario:
   - Username: `admin`
   - Password: anotalo para luego
   - Full name: tu nombre (opcional)
   - Email: cualquier email válido

5. Confirma URL de Jenkins: `http://localhost:8080` (por defecto está bien).
6. Finaliza setup.

---

### Paso 3 — Verificar plugins instalados

Desde interfaz de Jenkins:

- Clic en "Administrar Jenkins" (arriba derecha).
- Clic en "Administrar plugins".
- Pestaña "Plugins instalados".

**Busca que existan:**

- Git plugin
- Pipeline (Declarative)

Si no están, instálalos desde pestaña "Mercado de plugins".

---

### Paso 4 — Crear primer job freestyle

1. Clic en "Nueva tarea" (arriba).
2. Nombre: `test-freestyle`
3. Elige "Freestyle job".
4. Clic "OK".

En la página de configuración:

- **Descripción:** escribe "Mi primer job en Jenkins"
- **Build:** sección "Ejecutar". Clic "Agregar paso de construcción".
- Elige "Ejecutar linea de comandos (shell)".
- En el cuadro de texto, escribe:
  ```bash
  echo "Hola desde Jenkins"
  date
  echo "Job ejecutado correctamente"
  ```

5. Clic "Guardar".

---

### Paso 5 — Ejecutar job freestyle

- Clic en "Construir ahora".
- En "Historial de compilaciones" (izquierda) aparecerá `#1`.
- Clic en `#1` y luego en "Salida de consola".

**Resultado esperado:**

```
Hola desde Jenkins
[fecha y hora actual]
Job ejecutado correctamente
```

---

### Paso 6 — Crear primer Jenkinsfile

En tu máquina local, crea carpeta y archivos:

```bash
mkdir mi-primer-jenkins-proyecto
cd mi-primer-jenkins-proyecto
```

Crea archivo `Jenkinsfile`:

```groovy
pipeline {
  agent any

  stages {
    stage('Build') {
      steps {
        echo '========== STAGE BUILD =========='
        echo 'Descargando dependencias'
        sh 'echo "Simulando: pip install -r requirements.txt"'
      }
    }

    stage('Test') {
      steps {
        echo '========== STAGE TEST =========='
        echo 'Ejecutando tests'
        sh 'echo "Simulando: pytest tests/"'
        sh 'echo "Tests pasados: 15/15"'
      }
    }

    stage('Report') {
      steps {
        echo '========== STAGE REPORT =========='
        sh 'date'
        echo 'Pipeline completada exitosamente'
      }
    }
  }

  post {
    always {
      echo '=== Finalizando pipeline ==='
    }
    success {
      echo 'Pipeline exitosa'
    }
    failure {
      echo 'Pipeline falló'
    }
  }
}
```

Crea también un archivo `README.md`:

```markdown
# Mi Primer Proyecto Jenkins

Pipeline simple para entender estructura de Jenkinsfile.

## Stages:
- Build: simulación de instalación
- Test: simulación de tests
- Report: reporte final
```

---

### Paso 7 — Subir a Git (opcional pero recomendado)

Si tienes cuenta en GitHub:

```bash
cd mi-primer-jenkins-proyecto
git init
git add .
git commit -m "Initial commit: primer Jenkinsfile"
git remote add origin https://github.com/TU_USUARIO/mi-primer-jenkins-proyecto.git
git branch -M main
git push -u origin main
```

---

### Paso 8 — Crear pipeline job en Jenkins

1. En Jenkins, clic "Nueva tarea".
2. Nombre: `test-pipeline-declarativa`
3. Elige "Pipeline".
4. Clic "OK".

En configuración:

- **Descripción:** "Mi primer pipeline declarativa"
- **Pipeline:** sección de abajo.
- **Definition:** elige "Pipeline script from SCM".
- **SCM:** elige "Git".
- **Repository URL:** pega URL de tu repositorio (o usa formato local si no tienes GitHub).

Si usas Git local sin repositorio remoto:

- Elige "Pipeline script" en lugar de "from SCM".
- Copia y pega el contenido del `Jenkinsfile` en el área de texto.

5. Clic "Guardar".

---

### Paso 9 — Ejecutar pipeline

- Clic "Construir ahora".
- Verás progreso visual de stages.
- Clic en la ejecución para ver detalles.

**Resultado esperado:**

```
BUILD PASS (stage Build ejecutada)
TEST PASS (stage Test ejecutada)
REPORT PASS (stage Report ejecutada)
Pipeline exitosa
```

---

### Paso 10 — Configurar trigger manual y explorar webhooks

En configuración del job pipeline:

- Pestaña "Build Triggers".
- Marca "Construir cuando se reciba una notificación GitLab" (si está disponible).
- O marca "Poll SCM" y pon `H/5 * * * *` (cada 5 minutos).

Guarda. Ahora Jenkins puede detectar cambios sin presionar manualmente "Construir ahora".

**Nota:** para webhooks reales necesitas URL de Jenkins accesible desde internet, que no es el caso en localhost. Eso se trabaja en entorno productivo.

---

## 5) Evidencias a entregar (capturas)

1. Jenkins dashboard con al menos 2 jobs creados.
2. Salida de consola del job freestyle.
3. Ejecución visual de pipeline con las 3 stages completadas.
4. Logs de la etapa "Report" mostrando fecha/hora.
5. (Opcional) configuración de triggers en Jenkins.

---

## 6) Errores frecuentes y soluciones

1. **Jenkins no arranca en Docker**  
   Verifica puerto 8080 no ocupado: `sudo lsof -i :8080` o `sudo netstat -tlnp | grep 8080`.

2. **Error "Contraseña inicial no funciona"**  
   Reinicia Jenkins: `sudo docker restart jenkins`.

3. **Error `Cannot connect to Git`**  
   Git plugin no instalado. Instálalo desde "Mercado de plugins".

4. **Stage falla con error de shell**  
   Usa `sh` en Linux/Mac, o revisa sintaxis bash.

5. **Jenkinsfile tiene errores de sintaxis**  
   Validate con: copia en Jenkins UI dentro de "Pipeline script", clic en "Validar" (si existe botón).

---

## 7) Criterio de éxito de la práctica

La práctica está completada cuando:

- Jenkins está funcionando en Docker en `http://localhost:8080`.
- Creaste y ejecutaste job freestyle exitosamente.
- Creaste y ejecutaste pipeline declarativa con 3 stages.
- Comprendes diferencia entre freestyle y pipeline.
- Conoces dónde se configura trigger manual.

---

## 8) Pasos siguientes

- Integra Jenkins con repositorio Git real.
- Configura webhook desde GitHub/GitLab.
- Amplía Jenkinsfile con etapas de test real y construcción de artefactos.
- En Módulo 5 aprenderás a agregar etapa de despliegue.
