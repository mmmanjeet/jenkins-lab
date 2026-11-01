#!/bin/sh
# Run from the django-notes-app directory after creating .venv and installing requirements.
set -eu
mkdir -p ci-artifacts/static
python_cmd=.venv/bin/python
run_check() {
    report=$1
    shift
    if "$@" > "ci-artifacts/$report.log" 2>&1; then
        cat "ci-artifacts/$report.log"
    else
        cat "ci-artifacts/$report.log"
        return 1
    fi
}
run_check checks "$python_cmd" manage.py check --settings=notesapp.ci_settings
run_check migrations "$python_cmd" manage.py migrate --noinput --settings=notesapp.ci_settings
run_check tests "$python_cmd" manage.py test api --verbosity=2 --settings=notesapp.ci_settings
printf 'Django system checks, SQLite migrations and API tests passed.\n' > ci-artifacts/result.txt
