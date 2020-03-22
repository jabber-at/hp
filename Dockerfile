# syntax = docker/dockerfile:experimental
ARG IMAGE=python:3.8.2-slim-buster

FROM $IMAGE as base
WORKDIR /usr/src/hp
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cach
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache --mount=type=cache,target=/var/lib/apt,id=apt-lib \
    apt-get update && apt-get dist-upgrade
RUN --mount=type=cache,target=/root/.cache/pip,id=pip \
    pip install -U pip setuptools

###############
# Test stage #
##############
FROM base as test

# Download Selenium
RUN mkdir -p /usr/src/contrib/selenium/
RUN wget -O /usr/src/contrib/selenium/geckodriver.tar.gz \
        https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
RUN tar xf /usr/src/contrib/selenium/geckodriver.tar.gz -C /usr/src/contrib/selenium/

# Install APT requirements
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache --mount=type=cache,target=/var/lib/apt,id=apt-lib \
    apt-get install -qy build-essential libgpgme-dev xvfb git-core wget firefox-esr x11-utils

# Install pip requirements
ADD requirements.txt requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,id=pip \
    pip install -r requirements.txt -r requirements-dev.txt

# Add source
ENV DJANGO_SETTINGS_MODULE=hp.test_settings
ADD tox.ini ./
ADD hp/ ./

# Start testing
RUN flake8 .
RUN isort --check-only --diff -rc .
RUN python -Wd manage.py check
RUN python manage.py test

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
