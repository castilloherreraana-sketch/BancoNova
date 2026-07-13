# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BancoNova is a simulated digital banking web app used as a DevOps/infra teaching project. The Flask app itself is intentionally small (login, dashboard, transfers, payments, history — all backed by in-memory/session data, no real database or persistence). The bulk of the repository is the infrastructure and deployment pipeline around that app: Docker, Ansible, Kubernetes, Terraform, and a GitHub Actions CI/CD pipeline that chains all of them together.

When working in this repo, changes to `app/app.py` are usually the smaller part of the task — check whether a change also needs to be reflected in the Docker image, Ansible env vars, k8s ConfigMaps, or the pipeline.

## Running the app locally

```bash
cd app
pip install -r requirements.txt
python app.py               # dev server on :5000 (reads PORT, AMBIENTE, VERSION, FLASK_DEBUG env vars)
```

Copy `.env` as a template for local env vars (`SECRET_KEY`, `AMBIENTE`, `VERSION`, `PORT`, `FLASK_DEBUG`). Never commit a real `.env`.

Login uses hardcoded users in `USUARIOS` in [app/app.py](app/app.py) (`ana.garcia`/`12345`, `admin`/`admin`) — there is no real auth backend.

Health check endpoint: `GET /health` → `{status, ambiente, version}`. Used by Docker `HEALTHCHECK`, k8s liveness/readiness probes, and the pipeline's post-deploy verification — keep it working and cheap.

## Docker

```bash
docker build -f docker/Dockerfile -t banconova-app:latest .
# or
docker compose -f docker/docker-compose.yml up --build
```

Multi-stage Alpine build (`builder` → `produccion`), runs as a non-root `banconova` user, serves via `gunicorn` (not the Flask dev server) on port 5000. Build context is the repo root, not `docker/` — the Dockerfile's `COPY` lines reference `app/...` paths accordingly. The dockerignore file lives at `docker/Dockerfile.dockerignore` (Docker's per-Dockerfile ignore naming convention: `<dockerfile-path-relative-to-context>.dockerignore` at the context root), so it's picked up automatically even though it sits inside `docker/` rather than at the repo root.

## Ansible (`ansible/`)

Two parallel ways to configure/deploy exist — know which one a task is about before editing:

- **Role-based** (`site.yml`, roles in `ansible/roles/{servidor_base,docker,banconova_app}`): the structured, current approach — one role per concern (base OS setup, Docker install, app deploy).
- **Monolithic** (`playbook.yml`): an older single-file playbook that does the same three blocks (BASE / DOCKER / APP) inline. Kept for reference/comparison — prefer editing the role-based version unless a task specifically targets `playbook.yml`.
- **`deploy.yml`**: fast-path playbook that only re-runs the `banconova_app` role (used by CI after the first full `site.yml`/`playbook.yml` run has configured the server).
- **`verify.yml`**: standalone post-deploy check (Docker running, container status, health endpoint) — run after either playbook to confirm an environment is healthy without re-applying any config.

Environment variables live in `ansible/group_vars/{all,desarrollo,produccion}.yml` — `all.yml` has shared values (app name, firewall ports), the per-environment files set `puerto_externo`, `flask_debug`, `log_level`, `replicas`, `restart_policy`. Both environments currently point at `127.0.0.1` via `ansible_connection=local` in `ansible/inventory.ini`.

```bash
cd ansible
ansible-playbook site.yml --limit desarrollo   # or produccion
ansible-playbook site.yml --tags app           # just the app role
ansible-playbook deploy.yml --limit produccion --extra-vars "app_version=X.Y.Z"
ansible-playbook verify.yml --limit desarrollo
```

All four playbooks pass `ansible-lint` (config: `ansible/.ansible-lint`) at the `production` profile — keep new tasks lint-clean: canonical FQCN module names (e.g. `ansible.posix.sysctl`, not `ansible.builtin.sysctl`), `true`/`false` not `yes`/`no`. The `Reiniciar contenedor BancoNova` handler (in both the role and `playbook.yml`) needs `comparisons: {'*': ignore}` on its `docker_container` task — without it, a bare restart re-declares the container with none of the port/volume/env config from the main deploy task and silently strips them (port mapping included), breaking the deployment on the next `.env` change.

## Kubernetes (`k8s/`)

Fully separate manifest trees per environment: `k8s/desarrollo/` and `k8s/produccion/` each have their own `namespace.yaml`, `configmap.yaml`, `deployment.yaml`, `service.yaml`. Production additionally has `hpa.yaml` (2–5 replicas, scales on 60% CPU). Deployments use `imagePullPolicy: Never` — the image must already be loaded into the cluster (see pipeline: `docker save` → `docker load`). NodePorts: desarrollo `30001`, produccion `30002`. Rolling updates use `maxUnavailable: 0` for zero-downtime.

If you change an env var the app depends on, update it in the corresponding `configmap.yaml`, not just in Ansible's `group_vars`.

## Terraform (`terraform/`)

Only provisions the Kubernetes-level scaffolding (namespaces + `ResourceQuota` for desarrollo/produccion), targeting a local Minikube cluster by default (`kube_context = "minikube"`). It does not manage the Docker image, deployments, or app config — those are k8s manifests/Ansible's job.

## Testing Ansible/Terraform locally on Windows

Neither tool runs natively as a control node on Windows — use WSL (`wsl -d <distro>`), which has its own apt-installable Ansible/Terraform. A few WSL-specific gotchas hit during setup:

- **`ansible.cfg` silently ignored under `/mnt/c/...`**: Windows-mounted paths (DrvFs) report every file as world-writable, and Ansible refuses to auto-load an `ansible.cfg` from a world-writable directory — it won't even honor `ANSIBLE_CONFIG` pointed at that same file. Workaround: copy the `ansible/` folder into WSL's native filesystem (e.g. `~/some-test-dir`) before running commands there.
- **Container builds fail DNS resolution inside WSL2**: `pip install`/`apt` inside a `docker build` can fail with connection errors even though the WSL host has internet, because the container's `/etc/resolv.conf` points at an unreachable DNS forwarder. Fix locally (not in the repo) by adding `"dns": ["8.8.8.8", "1.1.1.1"]` to `/etc/docker/daemon.json` inside WSL and restarting the docker service.
- **No live k8s cluster by default**: `terraform plan`/`apply` need a reachable context. Either install minikube inside WSL, or enable Docker Desktop's built-in Kubernetes (Settings → Kubernetes) and pass `-var kube_context=docker-desktop` (its kubeconfig needs copying into WSL's `~/.kube/config` — WSL2's localhost-forwarding makes the cluster reachable from there once it's copied in).

## CI/CD pipeline (`.github/workflows/pipeline.yml`)

Push-triggered, staged: `build` (flake8 + pytest, both non-blocking via `|| true`/`|| echo`) → `docker` (build + save image as artifact) → `deploy-desarrollo` (on `develop` push: Ansible playbook + k8s apply + health check against `:30001`) → `deploy-produccion` (on `main` push, needs desarrollo deploy to succeed first: same pattern against `:30002`, plus HPA manifest applied). Production deploys are gated behind a successful desarrollo deploy — there is no direct path from a PR to production.

Note there are currently no real tests in the repo (`pytest` step is a no-op) and flake8 failures don't fail the build — don't assume CI is a correctness gate.

## Editing conventions in this repo

- Comments and commit messages are in Spanish; match that when editing existing files (ansible tasks, playbook comments, etc.).
- Version numbers (`1.0.0`) are duplicated across `app/app.py` defaults, `docker/Dockerfile`, `ansible/group_vars/all.yml`, `ansible/inventory.ini`, `.github/workflows/pipeline.yml` (`APP_VERSION`), and `terraform/variables.tf`. There's no single source of truth — bumping the version means grepping for the old value across these files.
