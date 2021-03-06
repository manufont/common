# coding: utf-8
# Copyright (c) Qotto, 2017

from celery_once.helpers import queue_once_key
from django.conf import settings
from django.utils import timezone
from functools import wraps
from inspect import getcallargs

def mutex_task(app):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapper(*args, **kwargs):
            backend = app.backend
            call_args = getcallargs(wrapped, *args, **kwargs)
            task_name = app.gen_task_name(wrapped.__name__, wrapped.__module__)
            key = queue_once_key(task_name, call_args)
            now = int(timezone.now().timestamp())
            expiration_delay = settings.CELERY_MUTEX_TIMEOUT
            result = backend.get(key)
            if result:
                remaining = now - int(result)
                if remaining < 0:
                    return
            backend.set(key, now + expiration_delay)
            try:
                return wrapped(*args, **kwargs)
            finally:
                backend.delete(key)
        return wrapper
    return decorator
