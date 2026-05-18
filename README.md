# CaribeTechArena-Hackathon-2026

## Meet the Team

I want to state from the beginning that we did not know each other prior to the event, and I think that was a truly enriching experience that made the event more real. Working with people you know is fantastic and sure you can move faster and of course you can trust (or not) the work done by your peers and also know what their strengths and limitations are. The social dynamic is familiar and fluent. Working with people you don't know at all that come from different backgrounds, that have different interests and stack preferences is unmistakingly a challenge in itself.

It was interesting to find out that we were all considering in one way or another not to attend the event for various reasons a couple of days earlier. However, the event coordinator reached out to us via WhatsApp and put us in contact to see if we could form a team. I found out that they were quite approachable people, friendly, and eager to learn from the event. They did not care about the bounties, nor did I. We cared more about experiencing the challenge of tackling real business problems in a constrained time window (24 hours).

To my surprise they were quite open at my intention to participate without leveraging AI to generate the code on my behalf. To me that was a welcoming gesture and that's why at that moment I left behind any hesitation to participate in a team, for I was already prepared to operate in solo dev mode.

Last but not least here are the individuals that conformed the last minute team:

- **Full Stack Developer** Juan Díaz Castro
- **Systems Programmer** Misael Díaz-Maldonado
- **Frontend Engineer** David Perez Sarmiento
- **Cybersecurity Specialist** Esteban Espitia 

We all contributed to the development in one way or another, for code is not the only form of contribution. We lived focused discussions trying to understand the problem and finding out how to tackle it best with the tools at our disposal.

Juan is the true champion of this project by implementing the most important requirements of this challenge by leveraging AI to generate the code. He also was the one that advocated for taking advantage of *django* for rapid development because of its monolithic design. I checked the SQL queries and fixed a logic issue that the AI did not foresee because it did not have enough context about the provided dataset. I also pointed out the timezone issues, the original data lacked the timezone information and the hosting server for our app was in another timezone. I also had the chance to write a tiny code written in C to ingest SQLite with nutrition fact data based on openfood facts [database](https://world.openfoodfacts.org/data). Because the dataset was too large to export it all on time and understand it I asked AI to generate data based on it (and it's likely that it used other sources hardcoded into its training data). David and I worked alongside to prepare the presentation which was also assisted by AI but revised by us. We discussed what worked and what didn't and what the CEO would care about during our pitch presentation. And Esteban analyzed the code for vulnerabilities, we did not have the time to address them but documented them in this [issue](https://github.com/juanjh1/Byte/issues/8) on the original [repository](https://github.com/juanjh1/Byte). 

I am looking forward to the next opportunity to collaborate and I am sure they all share the same wish.

## Note

The text that follows has been left unmodified in the original language that it was
written, and the writting was AI assisted (as one can tell from a glance).

## BioFood Challenge - Hackathon 2026

Este es el backend de la aplicación **BioFood**, desarrollada para la gestión de alimentación escolar, control de alérgenos y seguimiento de transacciones en cafeterías.

## Tecnologías
- **Core**: Django 6.0.5
- **Base de Datos Local**: SQLite (para desarrollo rápido)
- **Base de Datos Externa**: PostgreSQL (biofooddb)
- **Otras**: python-dotenv, psycopg2-binary

## Instalación y Configuración

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

## Estructura de la Base de Datos
El proyecto está dividido en aplicaciones modulares:
- **School**: Gestión de colegios y administradores de cafetería.
- **Student**: Perfiles de estudiantes, saldos y alérgenos.
- **Product**: Catálogo de productos y alérgenos alimentarios.
- **Transaction**: Registro de ventas y recargas de saldo.
- **Cafeteria**: Inventario y stock por colegio.
- **Parent**: Mapeo de padres a estudiantes por número de teléfono.
- **Chat**: Gestión de sesiones para comunicación/chatbot.

## Importación de Datos Reales
Para poblar tu base de datos local con los millones de registros de la base de datos externa:
1. Asegúrate de que `DB_CONNECTION=sqlite` esté en tu `.env`.
2. Ejecuta el script de importación masiva:
   ```bash
   python import_all_data.py
   ```
   *Nota: Este script importa todos los colegios, estudiantes, recargas y ventas (procesando millones de registros por lotes).*

## Ejecución
```bash
python manage.py runserver
```
Accede al panel de administración en: `http://127.0.0.1:8000/admin/`

## Features Clave

| Feature | Estado | Descripción |
|---------|--------|-------------|
| ✅ US-01 — Consulta conversacional padre | Implementado | "¿Qué comió Juan hoy?" → responde en tiempo real |
| ✅ US-02 — Alerta ausencia consumo | Implementado | Envía WhatsApp si no compró nada antes del mediodía |
| ✅ US-03 — Alerta crítica alérgeno | Implementado | Trigger inmediato + fallback cron (Signal + Cron) |
| ✅ US-04 — Proyección saldo | Implementado | Calcula fecha de agotamiento con pandas y margen ±2 días |
| ✅ US-05 — Alerta stock crítico | Implementado | Notifica a admins cuando stock ≤ mínimo |
| ⏳ US-06 — Resumen nutricional diario | En desarrollo | Próximo: resumen de calorías y nutrientes por estudiante |
| ⏳ US-07 — Recomendaciones personalizadas | En desarrollo | Sugerencias basadas en patrones de consumo |

---
*Hackathon BioFood 2026 - Alimentando el futuro!*
