#!/bin/sh -e

DATABASE_HOST=${DATABASE_HOST:-db}
DATABASE_PORT=${DATABASE_PORT:-5432}

while ! nc -z ${DATABASE_HOST} ${DATABASE_PORT}; do
    echo "Wait for ${DATABASE_HOST}:${DATABASE_PORT}..."
    sleep 0.1 # wait for 1/10 of the second before check again
done

python manage.py migrate --noinput
exec uwsgi --ini uwsgi.ini
