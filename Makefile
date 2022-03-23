py=python manage.py

run:
	$(py) runserver

migrate:
	$(py) makemigrations
	$(py) migrate

run-celery:
	celery -A core worker -l info --pool=solo
