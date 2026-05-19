# CaribeTechArena-Hackathon-2026

The [Caribe Tech Arena](https://www.caribetech.co/) is one of the most important events for software developers and enthusiasts in the Caribbean region during this Spring 2026.

The event took place in the First Living Lab of the Caribbean *Laboratorio Vivo* of the Universidad de la Costa (CUC) in Barranquilla Colombia. The main objective of the event was to connect talented software developers with local startups. The mentors of the event were tasked to identify developers that can tackle real business problems, these were presented by a handful of startups. The participants had to team up in groups of four and take key roles such as systems architect, product owner, frontend developer, and backend engineer. The teams were expected to leverage AI tools to deliver a Minimum Viable Product (MVP) in 24 hours sharp.

## Meet the team that formed out of serendipity

Team 8 [Dai hachi han (第八班)]: *Los Kuervos*

I want to state from the beginning that we did not know each other prior to the event, and I think that was a truly enriching experience that made the event more real. Working with people you know is fantastic and sure you can move faster and of course you can trust (or not) the work done by your peers and also know what their strengths and limitations are. The social dynamic is familiar and fluent. Working with people you don't know at all that come from different backgrounds, that have different interests and stack preferences is unmistakingly a challenge in itself.

It was interesting to find out that we were all considering in one way or another not to attend the event for various reasons a couple of days earlier. However, the event coordinator reached out to us via WhatsApp and put us in contact to see if we could form a team. I found out that they were quite approachable people, friendly, and eager to learn from the event. They did not care about the bounties, nor did I. We cared more about experiencing the challenge of tackling real business problems in a constrained time window (24 hours).

To my surprise they were quite open at my intention to participate without leveraging AI to generate the code on my behalf. To me that was a welcoming gesture and that's why at that moment I left behind any hesitation to participate in a team, for I was already prepared to operate in solo dev mode.

Last but not least here are the individuals that conformed the last minute team:

- Juan Díaz Castro **Full Stack Developer**
- Misael Díaz-Maldonado **Systems Programmer**
- David Perez Sarmiento **Frontend Engineer**
- Esteban Espitia **Cybersecurity Specialist**

We all contributed to the development in one way or another, for code is not the only form of contribution. We lived focused discussions trying to understand the problem and finding out how to tackle it best with the tools at our disposal.

Juan is the true champion of this project by implementing the most important requirements of this challenge by leveraging AI to generate the code. He also was the one that advocated for taking advantage of *django* for rapid development because of its monolithic design. I checked the SQL queries and fixed a logic issue that the AI did not foresee because it did not have enough context about the provided dataset. I noticed that truncation of the dataset without filtering by school would have meant pulling unrelated data, see commit [1f14dff](https://github.com/misael-diaz/CaribeTechArena-Hackathon-2026/blob/1f14dffb30cbcbd82863a1fb621356abf156989c). I also pointed out the timezone issues, the original data lacked the timezone information and the hosting server for our app was in another timezone. I also had the chance to write a lean code written in C to ingest SQLite with nutrition fact data based on openfood facts [database](https://world.openfoodfacts.org/data) (see commit [32ba223](https://github.com/misael-diaz/CaribeTechArena-Hackathon-2026/blob/32ba2238c91650eebd257573a4d1a921a54c93cd/ingest.c)). Because the dataset was too large to export it all on time and understand it I asked AI to generate data based on it (and it's likely that it used other sources hardcoded into its training data). David and I worked alongside to prepare the presentation which was also assisted by AI but revised by us. We discussed what worked and what didn't and what the CEO would care about during our pitch presentation. And Esteban analyzed the code for vulnerabilities, we did not have the time to address them but documented them in this [issue](https://github.com/juanjh1/Byte/issues/8) on the original [repository](https://github.com/juanjh1/Byte). 

I am looking forward to the next opportunity to collaborate and I am sure they all share the same wish.

## Mentors

We had the opportunity to speak with Oswaldo Saumet, he is the head of IT of *Medicos sin Fronteras*, he was a very approachable person with interest in advising on best practices with SQL databases. We also met Dario Guzmán, a startup founder, he shared with us his experiences with hackathons back when participants had to write all the code themselves. We also had the opportunity to meet Sergio Molinares, a cybersecurity expert, who came frequently to check on our progress. We are thankful for all the experiences and advice that they shared with us.

## Biofood Software

As a team we decided to pick the Biofood challenge because it resonated with our interests. We were tasked with improving Biofood Software, an app that connects parents, their children, and school cafeterias. Their software aims to solve two widespread problems in local schools, the problem of children having their money stolen and improving childhood nutrition habits. In a nutshell, [Biofood Software](https://biofoodsoftware.com/) is an app that notifies parents about what their children consume at school cafeterias, it enables kids to buy their meals with digital wallets, and it provides business analytics to school cafeterias. Their drive is to improve the quality of life and nutrition of children, inform parents about the nutritional values of the meals that the children consume, and aims to empower cafeterias with administrative dashboards  to manage their stock and keep track of their revenue.

We were presented with the challenge of delivering solutions that would prevent parents from sending their kids to school without enough credits to buy at the cafeteria (a win-win for everyone). We were also tasked with improving the nutritional information that the chatbot provides and to preemptively remind parents if the wallet balance is too low to make purchases. And also provide business intelligence to cafeterias by suggesting them popular products based on national data. This was in addition to building the entire dashboard application from scratch.

We focused mostly on the chatbot interaction with the parents and the nutritional analytics, for these were a novelty to all of us. We all have had our share of dealing with developing dashboards and decided to address the problems that were outside our comfort zone, that is, to delve into a new type of problem for us.

## Recommendations to Biofood

After watching the solutions presented by the other teams I noticed that some of them recommended settin up a system that would monitor and even allow parents to prevent their children from buying certain goods. At first this could seem to be a great feature, enabling parents to control what their children consume at school; however, as a parent myself I strongly disagree with that. First, healthy parent-child relationships are based on trust and communication. If you need to enforce something on your child maybe there's a problem. I am not a psychologist but the idea does not sound right to me. The other reason is that children like to share things with their friends or at least I hope that they still do because I am very fond of my childhood experiences. By blocking the ability of children to buy certain goods that could disrupt their natural behavior of sharing something nice that they may not even consume to their friends. Technological innovations should enrich social interactions, not disrupt them. They may not have the data to quantify how their app fosters children interactions but it might be as important as other metrics even if they are not as easy to correlate with revenue. I think it is worthwhile to investigate if there are hidden patterns in the dataset that can be discovered by means of Machine Learning (ML) and AI tools. 

Not all your clients want to receive notifications and you must provide a means for them to opt **in** and the **notification frequency** when they do; otherwise the default should be no notifications. If you disregard this your application behaves as a spamming application from the perspective of the clients that think this way. 

You should provide means to your clients to get charged automatically with caps in place. Why some of your clients would prefer this approach instead of being notified that their balance is low.

Do you actually need a chatbot to present the nutrition summary to your clients? No you don't need it. A simple Natural Language Processing (NLP) can infer the intent of a text message and that means that you can leverage that instead of a chatbot which will always cost a lot more because you own the NLP script, meaning zero token consumption. If you want to deliver the same with less research how you can introduce NLP into your business logic.

So my final recommendation is to thoroughly consider if you can do more with less, meaning that chatbots might be the trend now but that does not mean that they are the best solution.


## Lessons Learned

The hackathon was full with teams that delivered highly competitive solutions. This was a great experience for us to interact with other talented software developers. Here is what we learned.

- **Teamwork Matters**: The event was designed so that teams would solve real solutions as a coherent whole. AI did not count as a team member but as a tool; therefore, solo developers that delivered solutions by leveraging agentic workflows were not among the winners despite that they presented a highly polished and professional product. I cannot say that it was all due to not working as a team as the only factor but it clearly showed that it mattered because the work was truly impressive, nobody else came close to that.

- **Product Ownership Matters**: Solutions that were not closely aligned with the needs of the startups did not do that great either. Presenting a staggering web application without the conversational aspect that the owners wanted sent the wrong signal to them. I think it would have been better to work on what they cared the most even if you knew that the end product might not be as impressive in terms of visuals. Making their problem your own is even more important than trying to come up with an impressive but disconnected solution from the perspective of the startup founders.

- **Pitch Like a Pro**: It does not matter that your team completed every single milestone if the demo fails. Unfortunately, the code that we wrote or generated with AI does not enter into the equation on its own ground. They don't have time and no interest in the code, the code is your responsibility (even if generated by AI), and you get zero points if the demo does not run even if for a slight miscalculation. And even if you have a working demo but fail to connect with the founders from the beginning you will lose their attention almost instantly.

The Byte Arena was fierce and merciless and we all learned something from it.

## Conclusions: Beyond Chatbots

Talent is driven by the calling to solve challenging problems. I can understand no business wants to deliver less to clients now that AI makes it possible to develop solutions at rates never seen before (not necessarily of higher quality however if operating in unhinged mode). However, I don't think that doing just that is enough to scale and the startup founders surely know that. It all boils down to innovation. And what I mean about that is that talent is driven to solving innovative problems, I think that chabots are out of the vogue even if they can call us and have a conversation with us and take actions based on those interactions. Everyone is doing the same and when everyone is doing the same, especially in a hurry, it is less likely to innovate. You are not innovating, you are reacting to a trend.

My other concern is that I feel that apps are becoming too annoying by trying to predict my patterns and really it is disheartening from a user's perspective. I want performant software. What I don't want is software that is constantly changing and degrading over time. This goes to all the talented software developers that read this, you can work on more exciting problems than this and you will be glad that you followed this advice.

It would be great if next year we are challenged with problems beyond just conversational chatbots and dashboards. If you want to keep the local talent you may as well consider to level it up.

Nevertheless, I am thankful for the experience of collaborating in a team to address real business problems. The location was great, the mentors were outstanding, the food was delicious, the adrenaline levels were skyrocketing, and we were all having a great time while being considerate and respectful of others. I strongly recommend joining the Caribe Tech Arena next year because I know it is only going to get better.

## Notes

The text that follows has been left unmodified in the original language that it was
written, and the writing was AI assisted (as one can tell from a glance).

The kanji in the team section was generated by AI and alludes to the [Naruto](https://en.wikipedia.org/wiki/Naruto) series (the original team number was 7).

The team name was picked by Esteban, our cybersecurity specialist, and he is the only one that can explain the backstory for that name.

## Biofood Challenge - Hackathon 2026

Este es el backend de la aplicación **Biofood**, desarrollada para la gestión de alimentación escolar, control de alérgenos y seguimiento de transacciones en cafeterías.

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
*Hackathon Biofood 2026 - Alimentando el futuro!*
