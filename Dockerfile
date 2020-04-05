# syntax = docker/dockerfile:experimental
ARG IMAGE=python:3.8.2-slim-buster

FROM $IMAGE as base
WORKDIR /usr/src/hp
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cach
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache --mount=type=cache,target=/var/lib/apt,id=apt-lib \
    apt-get update && \
    apt-get -qy dist-upgrade && \
    apt-get -qy install netcat-openbsd libpq5
RUN --mount=type=cache,target=/root/.cache/pip,id=pip \
    pip install -U pip setuptools

FROM base as install
# Install APT requirements
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache --mount=type=cache,target=/var/lib/apt,id=apt-lib \
    apt-get update && \
    apt-get install -qy build-essential libgpgme-dev git-core gettext libpq-dev

ADD requirements.txt requirements-docker.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,id=pip \
    pip install --no-warn-script-location --prefix=/install -r requirements-docker.txt

###############
# Test stage #
##############
FROM base as test

# Install APT requirements
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache --mount=type=cache,target=/var/lib/apt,id=apt-lib \
    apt-get install -qy xvfb wget firefox-esr x11-utils

# Download Selenium
RUN mkdir -p /usr/src/contrib/selenium/
RUN wget -O /usr/src/contrib/selenium/geckodriver.tar.gz \
        https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
RUN tar xf /usr/src/contrib/selenium/geckodriver.tar.gz -C /usr/src/contrib/selenium/

# Install pip requirements
COPY --from=install /install /usr/local
ADD requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,id=pip \
    pip install -r requirements-dev.txt

# Add source
ENV DJANGO_SETTINGS_MODULE=hp.test_settings
ADD tox.ini ./
ADD hp/ ./

# Start testing
RUN flake8 .
RUN isort --check-only --diff -rc .
RUN python -Wd manage.py check
RUN python manage.py compilemessages -l de
RUN python manage.py test

FROM install as prepare
ADD hp/ ./
RUN mv hp/dockersettings.py hp/localsettings.py

COPY --from=install /install /usr/local
RUN python manage.py compilemessages -l de
RUN python manage.py collectstatic --no-input

# Cleanup source
RUN rm -rf core/tests account/tests/ hp/test_settings.py \
        core/static/lib/tinymce/src/ conversejs/static/lib/converse.js/tests \
        conversejs/static/lib/converse.js/docs/

RUN find . -type f -name "tests.py" -exec rm -rf {} \;
RUN find . -type f -name "*.pyc" -exec rm -rf {} \;
RUN find . -type d -empty -delete

FROM base
COPY uwsgi.sh files/uwsgi/uwsgi.ini .
COPY --from=prepare /var/www/hp/static /var/www/hp/static
COPY --from=install /install /usr/local
COPY --from=prepare /usr/src/hp /usr/src/hp
CMD /usr/src/hp/uwsgi.sh
