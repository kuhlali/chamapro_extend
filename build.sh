#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r chamapro/requirements.txt

python chamapro/manage.py collectstatic --no-input
python chamapro/manage.py migrate
