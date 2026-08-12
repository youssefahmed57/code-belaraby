# Deployment Architecture

## Source of truth

- `staging`
  - Repository-defined staging targets remain the validation reference.
  - `render.yaml` is the backend/worker parity definition for staging.
  - Mock execution and mock video providers must stay disabled.

- `production`
  - Production is managed by Coolify.
  - Frontend application: `code-belaraby-frontend-ssh` with base directory `frontend`
  - Backend application: `code-belaraby-backend-ssh` with base directory `backend`
  - GitHub `main` is the release source, but Coolify performs the actual deployment and routing.

## Deployment flow

1. Local verification and regression tests pass.
2. `Verify Platform` GitHub Actions passes on `main`.
3. Coolify pulls the verified `main` commit and rebuilds both applications.
4. Public smoke tests confirm:
   - frontend `/` returns `200`
   - backend `/api/v1/health` returns FastAPI JSON on the public host

## API routing

- Preferred production topology is same-origin:
  - `/` -> frontend
  - `/api/` -> backend
- Preferred frontend runtime configuration:
  - `NEXT_PUBLIC_API_URL=/api/v1`
- Use `BACKEND_INTERNAL_URL` only when the frontend must reach the backend by service hostname instead of reverse-proxy path routing.
- Production frontend must never point to staging backend infrastructure.

## Legacy artifacts

- `.github/workflows/deploy-production.yml`
  - Manual-only legacy reference. It does not SSH deploy production.
- `docker-compose.yml` and `docker-compose.production.yml`
  - CI validation and local production-like verification artifacts, not the authoritative live production deploy path while Coolify is active.
- `netlify.toml`, `vercel.json`
  - Non-authoritative unless intentionally re-adopted.
- `nginx/default.conf`
  - Local example only. The active production routing layer is Coolify/Traefik.

## Safety rules

- Never enable `ALLOW_LOCAL_RUNNER_IN_PROD=true`.
- Never enable `ALLOW_UNSAFE_LOCAL_CODE_EXECUTION=true`.
- Never enable `USE_MOCK_VIDEO_PROVIDER=true` in staging or production.
- Never enable `USE_MOCK_JUDGE0=true` in staging or production.
- Manual release actions must target a commit that already passed `Verify Platform`.
