This is an MVP of a job board that daily imports 80'000 Hours jobs board, adds extra tags (eg Software Engineering) and allows to subscribe to a fine-tuned search query.

Features:
- 80k import + possibility to post full details
- Customizable email alerts
- Job posts versioning (for managing multiple edit proposals)
- Extra fields + stackoverflow-like tagging system (salary, skills, workload type, generic tagging, etc)
- Comments

### Installation

- start postgres 14 and add its address to `.env.local.override` `DATABASE_URL` var
- Add the `hstore` connection to the database: `CREATE EXTENSION hstore;`
- poetry install
- python manage.py migrate
- python manage.py runserver

### Stack

Python 3.9, Django 3, Django Ninja, DRF, Algolia, Render
