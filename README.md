# BioFood - Hackathon 2026 🥗

Este es el backend de la aplicación **BioFood**, desarrollada para la gestión de alimentación escolar, control de alérgenos y seguimiento de transacciones en cafeterías.

## 🚀 Tecnologías
- **Core**: Django 6.0.5
- **Base de Datos Local**: SQLite (para desarrollo rápido)
- **Base de Datos Externa**: PostgreSQL (biofooddb)
- **Otras**: python-dotenv, psycopg2-binary

## 🛠️ Instalación y Configuración

1. **Clonar el repositorio** e instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   Crea un archivo `.env` en la raíz (ya existe uno de ejemplo generado) con las siguientes variables:
   ```env
   DB_CONNECTION=sqlite
   DB_HOST=3.208.123.187
   DB_PORT=5432
   DB_DATABASE=biofooddb
   DB_USERNAME=hackathon_dev
   DB_PASSWORD=PasswordHackaton2026
   SECRET_KEY=tu_secret_key
   DEBUG=True
   ```

3. **Aplicar Migraciones**:
   ```bash
   python manage.py migrate
   ```

4. **Crear Superusuario** (para el panel admin):
   ```bash
   python manage.py createsuperuser
   ```

## 📊 Estructura de la Base de Datos
El proyecto está dividido en aplicaciones modulares:
- **School**: Gestión de colegios y administradores de cafetería.
- **Student**: Perfiles de estudiantes, saldos y alérgenos.
- **Product**: Catálogo de productos y alérgenos alimentarios.
- **Transaction**: Registro de ventas y recargas de saldo.
- **Cafeteria**: Inventario y stock por colegio.
- **Parent**: Mapeo de padres a estudiantes por número de teléfono.
- **Chat**: Gestión de sesiones para comunicación/chatbot.

## 📥 Importación de Datos Reales
Para poblar tu base de datos local con los millones de registros de la base de datos externa:
1. Asegúrate de que `DB_CONNECTION=sqlite` esté en tu `.env`.
2. Ejecuta el script de importación masiva:
   ```bash
   python import_all_data.py
   ```
   *Nota: Este script importa todos los colegios, estudiantes, recargas y ventas (procesando millones de registros por lotes).*

## 🖥️ Ejecución
```bash
python manage.py runserver
```
Accede al panel de administración en: `http://127.0.0.1:8000/admin/`

---
*Hackathon BioFood 2026 - ¡Alimentando el futuro!* 🚀
