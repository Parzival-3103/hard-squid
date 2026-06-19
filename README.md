# Hard Squid

Tienda web de ropa deportiva con catálogo, carrito, compras, tickets y panel administrativo. El backend está construido con Flask (Python), el frontend con HTML/CSS/JavaScript y la información se guarda en MySQL.

## Funciones

- Catálogo por Dama, Caballero y Unisex, búsqueda y ficha de producto.
- Registro e inicio de sesión con contraseñas cifradas.
- Carrito, vista previa, validación de inventario, checkout y ticket imprimible.
- Historial de compras por cliente.
- Dashboard con ingresos, órdenes, usuarios, trabajadores, poco stock y artículos más vendidos.
- Alta, edición, baja y reactivación de productos con carga de imagen.
- Alta, baja y reactivación de trabajadores.
- Venta de mostrador y reporte exportable a CSV.
- Diseño adaptable a computadoras, tabletas y celulares.

## Instalación local con XAMPP

1. En XAMPP, inicia **MySQL**. Apache no es obligatorio porque Flask sirve la aplicación en el puerto 5000.
2. Instala [Python 3.11 o superior](https://www.python.org/downloads/) y abre PowerShell en esta carpeta.
3. Crea y activa un entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Copia `.env.example` como `.env`. Si el usuario `root` de MySQL tiene contraseña, agrégala en `DB_PASSWORD`.
5. Crea las tablas y el usuario administrador:

   ```powershell
   flask --app app init-db
   ```

6. Inicia la tienda:

   ```powershell
   flask --app app run --debug
   ```

7. Abre `http://127.0.0.1:5000`.

Si aparece el error `Can't connect to MySQL ... (10061)`, inicia MySQL desde el panel de XAMPP. Si XAMPP muestra que `ibdata1` no se puede escribir, cierra procesos antiguos de `mysqld`, abre el panel de XAMPP como administrador y vuelve a iniciar MySQL. No borres la carpeta `mysql/data`: podría contener otras bases de datos.

Administrador inicial: `admin@hardsquid.mx` / `Admin123!`. Cámbialo antes de publicar el sitio.

También puedes importar `schema.sql` desde phpMyAdmin; después ejecuta `flask --app app init-db` una vez para crear el administrador con contraseña cifrada.

## Publicar en GitHub

```powershell
git init
git add .
git commit -m "Tienda Hard Squid"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/hard-squid.git
git push -u origin main
```

GitHub almacena el código, pero no ejecuta Flask ni MySQL. Para que cualquiera pueda visitar la tienda con un link público hay que desplegarla en un servicio compatible con Python y usar una base MySQL alojada.

Guía rápida: revisa `DEPLOY.md`.

Configura allí las variables de `.env`; nunca subas el archivo `.env` ni claves reales al repositorio.

## Estructura principal

- `app.py`: rutas, autenticación, compras y administración.
- `schema.sql`: estructura MySQL y productos iniciales.
- `templates/`: vistas HTML de la tienda y el panel.
- `static/css/app.css`: identidad visual y diseño responsivo.
- `static/uploads/`: imágenes agregadas por administradores (no se versionan).

## Antes de producción

La pantalla de pago es una simulación académica y no cobra dinero. Para aceptar pagos reales, integra Stripe o Mercado Pago, usa HTTPS, cambia `SECRET_KEY`, cambia la contraseña inicial y desactiva `FLASK_DEBUG`.
