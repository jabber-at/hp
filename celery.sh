#!/bin/sh -e

CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

# exec celery worker -A hp --loglevel=${CELERY_LOGLEVEL} -B -s /var/lib/hp/celery.schedule
exec celery worker -A hp -B -s /var/lib/hp/celery.schedule
