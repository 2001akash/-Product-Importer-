from celery import Celery
import os

broker = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1')
backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')

celery = Celery('tasks', broker=broker, backend=backend)

celery.conf.task_serializer = 'json'
celery.conf.result_serializer = 'json'
celery.conf.accept_content = ['json']
celery.conf.worker_max_tasks_per_child = 100
