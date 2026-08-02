# ⚠️ 02. Risk Register & Vulnerability Assessment

**Audit Date**: 2026-08-02  
**Branch**: `production-readiness-audit`  

---

## Risk Severity Matrix

| Risk ID | Category | Description | Original Severity | Mitigation Status | Current Risk Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | Security / Execution | Local Subprocess executor running in production environment | **BLOCKER** | Enforced check in `ExecutionService.run_code_sync` throwing `RuntimeError` if `ENVIRONMENT=production`. | **RESOLVED / CONTROLLED** |
| **RISK-02** | Data Integrity | Monolithic single DB create script bypassing migrations | **CRITICAL** | All models mapped in Alembic `001_initial_schema.py`. Seed script uses DB session inserts. | **RESOLVED** |
| **RISK-03** | Auth / RBAC | Student accessing admin endpoints or another student's receipts | **CRITICAL** | Enforced RBAC dependencies (`require_roles(["admin"])`) and student-ID check on receipts. | **RESOLVED** |
| **RISK-04** | Security | Exposing quiz answers / `is_correct` in network responses | **CRITICAL** | `start_quiz` strips `is_correct` from option payloads before returning JSON. | **RESOLVED** |
| **RISK-05** | Integrations | Judge0, Cloudflare Stream, n8n running in mock mode without production credentials | **HIGH** | Explicitly documented as `Pending Credentials` / `Mocked`. PROD fallback guards in place. | **ACCEPTED / PENDING PROD DEPLOYMENT** |
| **RISK-06** | DevOps | Database passwords and JWT secrets using default development fallbacks | **HIGH** | Secrets isolated to `.env`, startup check validates non-empty secrets. | **ACTION REQUIRED FOR PROD DEPLOYMENT** |
