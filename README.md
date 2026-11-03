# DevOps Capstone Project

[![Continuous Integration](https://github.com/axsh06/devops-capstone-project/actions/workflows/ci-build.yaml/badge.svg?branch=codex%2Fdevops-capstone)](https://github.com/axsh06/devops-capstone-project/actions/workflows/ci-build.yaml)

Customer accounts REST API for the IBM DevOps capstone, implemented with Flask
and PostgreSQL. Includes automated tests, GitHub Actions CI, browser security
headers, CORS, Docker packaging, Kubernetes manifests, and a Tekton CD pipeline.

## API

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | `/health` | Service health |
| GET | `/` | API information |
| POST | `/accounts` | Create an account; returns 201 and Location |
| GET | `/accounts` | List accounts |
| GET | `/accounts/{id}` | Read an account |
| PUT | `/accounts/{id}` | Update an account |
| DELETE | `/accounts/{id}` | Delete an account; returns 204 |

Missing resources return 404. Invalid payloads and content types return 400
and 415. Tests cover persistence, error handling, security headers, HTTPS
redirects, allowed/rejected CORS origins, and preflight requests.

## Development and validation

The course environment uses Python 3.9. Initialize it with `source bin/setup.sh`,
then run `nosetests`. The 32-test suite enforces at least 95% service coverage.
CI provisions PostgreSQL, installs dependencies, runs Flake8, and runs the tests.

Set `DATABASE_URI` for the database connection. Alternatively, provide
`DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, and `DATABASE_PASSWORD`.
Set `SECRET_KEY` when using the service outside the disposable course lab.

HTTPS redirects are enabled by default. For a local HTTP-only lab container,
set `FORCE_HTTPS=false`. `CORS_ORIGINS` is a comma-separated allowlist, defaulting
to `http://localhost:3000`; cross-origin credentials are disabled.

## Docker and Kubernetes

Build with `docker build -t accounts:1 .`. The image runs Gunicorn as a non-root
user on port 8080. The `deploy/` manifests define three replicas, readiness and
liveness probes, a NodePort service, and an OpenShift edge-TLS route.

Provision the PostgreSQL template, replace `IMAGE_NAME_HERE` in the deployment
with your registry image, and apply the manifests. Database credentials come
from the `postgresql` Kubernetes Secret. Health probes identify the forwarded
HTTPS scheme because TLS terminates at the OpenShift route.

## Continuous delivery

Apply `tekton/pvc.yaml`, `tekton/tasks.yaml`, and `tekton/pipeline.yaml`; install
the Tekton Catalog `git-clone` task. The lab supplies `buildah` and
`openshift-client` ClusterTasks and the `pipeline` service account.

The pipeline cleans its dedicated workspace, clones the selected revision,
runs lint and tests, builds/pushes the image, applies manifests, and waits for
a successful rollout. Required parameters are `repo-url` and `build-image`;
`branch` selects the source revision. Bind `pipeline-workspace` to
`pipelinerun-pvc`.

`bin/collect-rest-evidence.sh` exercises a synthetic account and saves the
actual curl commands and responses under `evidence/`.

## License

Apache License 2.0. Based on the IBM Skills Network capstone starter project.
