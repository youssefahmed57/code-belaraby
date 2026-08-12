# Deployment Architecture

## Authoritative environments

- `staging`
  - Frontend: Vercel staging deployment
  - Backend: Render web + worker services
  - Sandbox execution: external Judge0 or equivalent isolated runner
  - Video provider: real private provider credentials only

- `production`
  - Frontend: production Vercel deployment with production domain
  - Backend: VPS deployment using `docker-compose.yml` plus `docker-compose.production.yml`
  - Reverse proxy / TLS: host nginx using `deploy/nginx/production.conf`
  - Sandbox execution: external Judge0 or equivalent isolated runner

## Non-authoritative legacy files

- `netlify.toml`
  - Legacy preview-only artifact. Not an active staging or production target.
- `nginx/default.conf`
  - Legacy local reverse-proxy example. Production should use `deploy/nginx/*.conf`.

## API routing rules

- Frontend must use `NEXT_PUBLIC_API_URL`.
- `vercel.json` must not hardcode a staging backend rewrite.
- Staging frontend points only to staging backend.
- Production frontend points only to production backend.

## Deployment gate

- Production deployment is triggered only after the `Verify Platform` workflow succeeds.
- Direct `push` to `main` no longer deploys immediately.
