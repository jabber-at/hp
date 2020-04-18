ARG IMAGE=python:3.8.2-slim-buster

FROM $IMAGE as base
WORKDIR /usr/src/hp
RUN apt-get update && \
    apt-get -qy dist-upgrade && \
    apt-get -qy install --no-install-recommends netcat-openbsd libpq5 && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache -U pip setuptools

FROM base as install
# Install APT requirements
RUN apt-get update && \
    apt-get install -qy --no-install-recommends build-essential libgpgme-dev git-core gettext libpq-dev && \
    rm -rf /var/lib/apt/lists/*

ADD requirements.txt requirements-docker.txt ./
RUN pip install --no-cache --no-warn-script-location --prefix=/install -r requirements-docker.txt

###############
# Test stage #
##############
FROM base as test

# Install APT requirements
RUN apt-get update && \
    apt-get -qy dist-upgrade && \
    apt-get install -qy build-essential xvfb wget firefox-esr x11-utils gettext && \
    rm -rf /var/lib/apt/lists/*

# Download Selenium: https://github.com/mozilla/geckodriver/releases
RUN mkdir -p /usr/src/contrib/selenium/
RUN wget --quiet -O /usr/src/contrib/selenium/geckodriver.tar.gz \
        https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
RUN tar xf /usr/src/contrib/selenium/geckodriver.tar.gz -C /usr/src/contrib/selenium/

# Install pip requirements
COPY --from=install /install /usr/local
ADD requirements-dev.txt ./
RUN pip install --no-cache -r requirements-dev.txt

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
RUN find . -type f -name "*.po" -exec rm -rf {} \;
RUN find conversejs/static/lib -type f | egrep -v '(converse.js/css/converse.css|converse.js/dist/converse.js)' | xargs rm
RUN find . -type d -empty -delete

FROM base
COPY uwsgi.sh files/uwsgi/uwsgi.ini ./
COPY --from=prepare /var/www/hp/static /var/www/hp/static
COPY --from=install /install /usr/local
COPY --from=prepare /usr/src/hp /usr/src/hp
CMD /usr/src/hp/uwsgi.sh
