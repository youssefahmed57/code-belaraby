# Deployment Architecture

> Superseded reference. As of Wednesday, August 12, 2026, the authoritative deployment split is documented in `docs/deployment-architecture.md`. This file is retained only for historical context.

## Authoritative Deployment

The platform uses Docker Compose with environment-specific overrides.

### Production
```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Required environment variables (set in `.env` on VPS):
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `CSRF_SECRET`
- `SIGNED_URL_SECRET`
- `COOKIE_DOMAIN`
- `ALLOWED_ORIGINS`
- `DATABASE_URL`

### Staging
```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
```

## Legacy / Deprecated Paths

The following deployment configurations exist but are NOT the primary deployment method:

- `vercel.json` — Frontend-only deployment to Vercel (deprecated in favor of Docker)
- `render.yaml` — Render.com deployment (deprecated)
- `netlify.toml` — Netlify deployment (deprecated)

These files are retained for reference but should NOT be used for production deployments.

## Frontend API URL

The frontend reads `NEXT_PUBLIC_API_URL` at build time.

- **Production**: Set to the production backend URL
- **Staging**: Set to the staging backend URL
- **Development**: Defaults to `http://localhost:8000/api/v1`

> **CRITICAL**: Production frontend must NEVER use a staging or development backend URL.

## CI/CD

Production deployment no longer runs directly on every push to `main`.
The repository now gates deployment behind the verification workflow, migration validation, and Docker config validation before the production workflow can proceed.
