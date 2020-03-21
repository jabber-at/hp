# syntax = docker/dockerfile:experimental
ARG IMAGE=python:3.8.1-alpine3.11

FROM $IMAGE as base
WORKDIR /usr/src/hp
RUN --mount=type=cache,target=/etc/apk/cache apk upgrade

FROM base as test
RUN --mount=type=cache,target=/etc/apk/cache apk add --update \
        build-base libffi-dev libxml2-dev gpgme-dev libxslt-dev jpeg-dev git
ADD requirements.txt requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt -r requirements-dev.txt

ENV DJANGO_SETTINGS_MODULE=hp.test_settings
ADD tox.ini ./
ADD hp/ ./
RUN flake8 .
RUN isort --check-only --diff -rc .
RUN python -Wd manage.py check
RUN VIRTUAL_DISPLAY=y python manage.py test

FROM $IMAGE as build
WORKDIR /usr/src/hp
RUN --mount=type=cache,target=/etc/apk/cache apk upgrade
ADD requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install \
        --no-warn-script-location --prefix=/install -r requirements.txt


FROM $IMAGE
WORKDIR /usr/src/hp
RUN apk --no-cache upgrade && apk add --no-cache libpq
COPY --from=build /install /usr/local

ADD hp/ hp/

RUN ln -s /usr/local/bin/manage /usr/src/hp/hp/manage.py
