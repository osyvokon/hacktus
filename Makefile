all: worker server

server:
	python run.py

worker:
	mkdir -p logs
	celery worker -b redis://localhost:6379 --app=app.github_task --purge --detach --logfile=logs/workers.log
