# Deployment Notes

This repository's active production deployment platform is Coolify, not direct SSH Docker Compose.

## Production

- Coolify application `code-belaraby-backend-ssh`
  - repository: `youssefahmed57/code-belaraby`
  - branch: `main`
  - base directory: `backend`

- Coolify application `code-belaraby-frontend-ssh`
  - repository: `youssefahmed57/code-belaraby`
  - branch: `main`
  - base directory: `frontend`

- Production release sequence:
  1. local verification
  2. green `Verify Platform`
  3. Coolify redeploy of the verified commit

## Staging

- `render.yaml` is the repository-owned staging definition for backend and worker parity checks.
- Staging must also disable mock execution and mock video providers.

## Compose files

- `docker-compose.yml` and `docker-compose.production.yml` remain important for:
  - local production-like validation
  - Docker config checks in CI
  - documenting required runtime variables
- They are not the authoritative live production deployment mechanism while Coolify is in use.

## Frontend API configuration

- Preferred production configuration:
  - `NEXT_PUBLIC_API_URL=/api/v1`
  - reverse proxy routes `/api/*` to the backend service
- If path-based proxying is unavailable, set `BACKEND_INTERNAL_URL` to a real backend origin reachable from the frontend container.
- Never point production frontend traffic to staging infrastructure.

## Authentication contract

- Browser-facing sessions remain anchored in HttpOnly cookies.
- Login and registration responses still include `access_token` for repository-owned automated tests and non-browser API consumers that already depend on bearer auth.
- Frontend application state must not persist bearer tokens in `localStorage`.

## Execution architecture

- Public coding endpoints currently use a bounded synchronous execution request flow.
- The Redis worker exists for queued execution jobs, but frontend/API submissions are not yet routed through that queue.
- Safety controls for the current request flow must stay enabled:
  - strict input-size caps
  - capped test-case counts
  - explicit request deadlines
  - fail-closed behavior when isolated execution is required and unavailable

## Legacy workflow

- `.github/workflows/deploy-production.yml` is manual-only and intentionally does not SSH deploy production.
- Missing VPS SSH secrets should no longer create a false red production-deploy signal after a successful CI run.
