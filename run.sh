#!/bin/sh
set -x


if [ "$1" = "web" ];
then

    echo "==================="
    echo "Running web"
    echo "==================="
    echo
    python manage.py migrate
    python manage.py loaddata auth.json
    python manage.py collectstatic --no-input
    python manage.py runserver 0.0.0.0:9000    

elif [ "$1" = "worker" ]
then

    echo "======================"
    echo "Running celery worker"
    echo "======================"
    echo
    celery worker -A shipping --loglevel=INFO

fi