#!/usr/bin/env bash
set -o errexit

# requirements.txt se genera con uv export (no se edita a mano)
pip install -r requirements.txt

cd src
python manage.py collectstatic --no-input
python manage.py migrate

# SQLite se borra en cada deploy: se vuelven a cargar los datos de demo
python manage.py loaddata usuarios catalogo ventas eventos
