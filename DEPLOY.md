# Publicar Hard Squid con link público

GitHub solo guarda el código. Para que cualquiera abra la tienda con un link necesitas un hosting que ejecute Flask y una base de datos MySQL en la nube.

## Opción recomendada: Railway

Railway es práctico para este proyecto porque puedes tener la app Flask y MySQL en el mismo panel.

### 1. Sube el proyecto a GitHub

Desde PowerShell:

```powershell
cd C:\xampp\htdocs\repos
git add .
git commit -m "Preparar Hard Squid para despliegue"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/hard-squid.git
git push -u origin main
```

Si ya existe `origin`:

```powershell
git remote set-url origin https://github.com/TU_USUARIO/hard-squid.git
git push -u origin main
```

### 2. Crea el proyecto en Railway

1. Entra a Railway.
2. Crea un nuevo proyecto desde tu repositorio de GitHub.
3. Agrega un servicio de base de datos MySQL.
4. En el servicio de la app Flask, configura las variables de entorno.

### 3. Variables de entorno

Configura estas variables en el hosting:

```env
DB_HOST=host_de_mysql
DB_PORT=3306
DB_NAME=nombre_de_tu_base
DB_USER=usuario_mysql
DB_PASSWORD=password_mysql
SECRET_KEY=pon_una_clave_larga_y_segura
FLASK_DEBUG=0
```

En XAMPP local puedes seguir usando:

```env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_NAME=hard_squid
DB_USER=root
DB_PASSWORD=
```

### 4. Comando de inicio

El proyecto ya incluye `Procfile`:

```text
web: gunicorn app:app
```

Eso le dice al hosting cómo iniciar Flask.

### 5. Inicializar la base de datos

Después del primer deploy, abre una consola del hosting y ejecuta:

```bash
flask --app app init-db
```

Eso crea tablas, productos iniciales y el administrador:

- Correo: `admin@hardsquid.mx`
- Contraseña: `Admin123!`

### 6. Link público

Cuando el deploy termine, Railway te dará un dominio público. Ese es el link que puedes compartir para que cualquiera entre sin instalar nada.

Ejemplo:

```text
https://hard-squid.up.railway.app
```

## Nota importante sobre imágenes subidas

En hosting gratuito, los archivos subidos localmente pueden perderse si el servidor se reinicia. Para un proyecto escolar está bien; para una tienda real conviene guardar imágenes en Cloudinary, S3 o similar.
