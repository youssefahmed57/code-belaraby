# 🌐 04. Environment Configuration & Matrix Report

> Historical snapshot from Saturday, August 2, 2026. This file is not the current deployment authority and may describe pre-hardening defaults. For the active production/staging design and required secrets, use `docs/deployment-architecture.md` plus the current environment templates.

**Audit Date**: 2026-08-02  
**Branch**: `production-readiness-audit`  

---

## 1. Environment Configuration Table

| Environment Variable | Service | Required / Optional | Development Default | Production Requirement | Is Secret? | Current Validation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Backend / Frontend | Required | `development` | `production` | No | 🟢 Verified |
| `LOG_LEVEL` | Backend | Optional | `INFO` | `INFO` / `WARNING` | No | 🟢 Verified |
| `SECRET_KEY` | Backend | Required | `dev_super_secret_key...` | Cryptographically Random 64+ char string | **YES** | ⚠️ Dev Default (Rotate in PROD) |
| `CSRF_SECRET` | Backend | Required | `csrf_super_secret_key...` | Cryptographically Random 32+ char string | **YES** | ⚠️ Dev Default (Rotate in PROD) |
| `ALLOWED_ORIGINS` | Backend | Required | `["http://localhost:3000"]` | `["https://codejourney.academy"]` | No | 🟢 Configurable |
| `COOKIE_DOMAIN` | Backend | Required | `localhost` | `.codejourney.academy` | No | 🟢 Configurable |
| `SECURE_COOKIES` | Backend | Required | `false` | `true` | No | 🟢 Configurable |
| `DATABASE_URL` | Backend | Required | `postgresql+asyncpg://...` | Production PostgreSQL Pool | **YES** | 🟢 PostgreSQL Active |
| `SYNC_DATABASE_URL` | Backend | Required | `postgresql://...` | Production PostgreSQL Sync | **YES** | 🟢 PostgreSQL Active |
| `REDIS_URL` | Backend | Required | `redis://localhost:6379/0` | Production Redis Instance | **YES** | 🟢 Configured |
| `JUDGE0_URL` | Backend | Required in PROD | `http://judge0:2358` | Production Judge0 Sandbox Instance | No | 🟡 Mocked / Pending Creds |
| `CLOUDFLARE_STREAM_ACCOUNT_ID`| Backend | Optional in Dev | `mock_cf_account` | Cloudflare Stream Account ID | **YES** | 🟡 Mocked / Pending Creds |
| `STORAGE_PROVIDER` | Backend | Required | `local` | `r2` / `s3` / `local` | No | 🟢 Local Active |
| `NEXT_PUBLIC_API_URL` | Frontend | Required | `http://localhost:8000/api/v1` | `https://api.codejourney.academy/api/v1` | No | 🟢 Configurable |
| `NEXT_PUBLIC_APP_URL` | Frontend | Required | `http://localhost:3000` | `https://codejourney.academy` | No | 🟢 Configurable |
