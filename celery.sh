#!/bin/sh -e

exec celery worker -A hp --loglevel=INFO -B -s /var/lib/hp/celery.schedule
