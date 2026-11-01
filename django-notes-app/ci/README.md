# Django Jenkins pipeline fix: kya aur kyon change hua

## Original pipeline kyon fail thi

Original Jenkinsfile kisi aur Jenkins environment ke liye thi:

- `@Library('Shared')` ke liye valid Shared Library configuration/repository/version chahiye thi.
- `dev-server` agent label is lab mein configured nahi tha.
- `clone`, `dockerbuild`, `dockerpush`, aur `deploy` custom library functions the, standard Jenkins steps nahi.
- Current agents mein Docker daemon/build engine nahi hai, aur Jenkins mein Docker Hub credential configured nahi mila.

Original local Jenkinsfile ka backup Ubuntu mein `/home/ubuntu/jenkins-docker/backups/django-pipeline-before-fix/Jenkinsfile` par hai.

## New scope: runnable backend CI

This fix checks out your repository, installs backend dependencies, checks Django, applies isolated SQLite migrations, runs two real API smoke tests, and archives reports. It **does not build/push a Docker image or deploy the application**. Those old custom stages are replaced by CI checks, not silently claimed as working. Image publishing needs a chosen build engine, registry/repository and Jenkins credentials; deployment needs an explicit target and access configuration.

No Shared Library is needed for this version. The app's normal MySQL settings, Dockerfile, Docker Compose, production database, and existing Jenkins jobs were not modified.

## Changed files

| File | Reason |
| --- | --- |
| `../Jenkinsfile` | Use configured Kubernetes cloud/template and standard Pipeline steps |
| `../notesapp/ci_settings.py` | CI-only SQLite database; no MySQL service or .env needed |
| `../api/test_ci.py` | Verify empty notes response and full note create/read/update/delete lifecycle |
| `run.sh` | Run checks/migrations/tests with failure propagation and save reports |
| `../.gitignore` | Ignore virtualenv, CI database/reports and local config for future untracked files |

Adding ignore rules does not remove files already tracked in Git. This change does not delete any local .env or database or rewrite Git history.

## Flow

```text
Jenkins job reads django-notes-app/Jenkinsfile from SCM
  -> Kubernetes plugin uses cloud kind-kubernetes
     -> inherits template kind-agent
        -> merges an additional Python container into the agent Pod
           -> jnlp container: checkout scm
           -> python container: install requirements in workspace .venv
           -> python container: sh ci/run.sh
           -> controller archives ci-artifacts reports
           -> temporary agent Pod/workspace cleaned up
```

`inheritFrom 'kind-agent'` refers to the Pod template name. `cloud 'kind-kubernetes'` is the Cloud name. `yamlMergeStrategy merge()` preserves the parent's worker affinity, security context and jnlp container while adding Python. Both containers share the agent workspace; source checkout is done in jnlp because that image already has Git. Python is installed in its own image, not in the controller.

The Python container uses `sleep 99d` only to stay available for Pipeline exec commands. It does not keep the Pod for 99 days: normal agent lifecycle deletes the Pod after the build releases it.

`skipDefaultCheckout(true)` prevents duplicate implicit checkout. The explicit `checkout scm` uses the repository/branch/credential from this Pipeline job. It checks out your own repo, not the original author's repository. The code path is `django-notes-app/` inside the outer repo workspace.

The pipeline uses a 15-minute timeout and disallows concurrent builds of this job. It does not disable concurrent builds across other jobs.

## What the checks do

The Python container creates `.venv` and installs the existing pinned `requirements.txt`. `ci/run.sh` then executes:

```bash
.venv/bin/python manage.py check --settings=notesapp.ci_settings
.venv/bin/python manage.py migrate --noinput --settings=notesapp.ci_settings
.venv/bin/python manage.py test api --verbosity=2 --settings=notesapp.ci_settings
```

CI settings import the normal application settings but override the database with a temporary SQLite file, an explicit test-only secret, and CI static-file locations. Tests use Django's isolated test database. This validates backend behavior with SQLite; it does not validate MySQL-specific behavior or compile/test the React frontend.

The two API tests exercise the real application URLs and views:

- Initially, `/api/notes/` returns an empty list.
- A note can be created, read, updated and deleted through the API.

Any failing command returns nonzero and fails the build. Reports are archived in the pipeline's `post { always { ... } }` block even when a check fails. `result.txt` is written only after all checks succeed.

## Build artifacts

From the Jenkins job, select the build number and **Build Artifacts**:

- `commit.txt`: actual checked-out revision.
- `checks.log`: Django system checks.
- `migrations.log`: migration output.
- `tests.log`: actual test results.
- `result.txt`: success report, present only if all checks passed.

Agent workspace deletion does not remove these archived reports. Controller storage retains them until build/artifact retention or manual deletion removes them.

## Validation performed locally

- The Jenkins controller's installed Groovy parser accepted the Jenkinsfile syntax. This is a syntax check, not a complete Jenkins Declarative-model/integration validation.
- Shell syntax (`sh -n`) and Git whitespace (`git diff --check`) passed.
- A fresh `python:3.11-slim` Docker container running UID/GID 1000 installed the dependencies and executed the same CI script on an isolated copy without .env or the local database.
- Django system checks passed, SQLite migrations passed, and **2 API tests passed**.
- No Git commit/push, Docker Hub publish, production deploy, controller restart or job configuration change was performed for this fix.

A full Jenkins/Kubernetes run still needs the changed files committed and pushed so the SCM job can fetch them. The first Python image pull on a worker can take time.

## Commit, push, run

From `/mnt/c/Users/hp/Documents/jenkins-pipeline`:

```bash
git diff -- django-notes-app/Jenkinsfile django-notes-app/.gitignore
git add django-notes-app/Jenkinsfile django-notes-app/.gitignore \
  django-notes-app/notesapp/ci_settings.py django-notes-app/api/test_ci.py \
  django-notes-app/ci
git commit -m "Fix Django CI pipeline for kind agents"
git push origin main
```

In job `Django-notes-app-pipeline`, keep **Pipeline script from SCM** with your repo and Script Path **django-notes-app/Jenkinsfile**. Run **Build Now** once after the push, or wait for its configured SCM trigger. Do not create a Cloud named dev-server for this file; it uses the existing working cloud/template.
