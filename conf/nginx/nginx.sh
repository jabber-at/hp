#!/bin/sh -ex

NGINX_CONFIG=/etc/nginx/sites-available/${NGINX_CONFIG:-localhost.conf}

if [ ! -e ${NGINX_CONFIG} ]; then
    echo "Error: $NGINX_CONFIG: No such file or directory."
    exit 1
fi

envsubst < ${NGINX_CONFIG} > /etc/nginx/conf.d/default.conf

nginx -g 'daemon off;'
