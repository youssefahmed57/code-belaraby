# 🐛 Defect Tracking Log & Resolution Audit

**Audit Date**: 2026-08-02  
**Branch**: `production-readiness-audit`  

---

## Defect Summary

| Defect ID | Component | Severity | Description | Root Cause | Status & Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | Student Dashboard | **HIGH** | Dashboard rendered hardcoded course cards and duplicated 80% progress | Frontend mapped over `/courses` public catalogue endpoint instead of active student enrolments | **RESOLVED**: Created `/dashboard/summary` endpoint returning active enrolments and independent progress. |
| **DEF-02** | Monaco Code Playground | **HIGH** | Monaco Editor displayed blank grey area with SSR error | Client-side Monaco required dynamic import with `{ ssr: false }` | **RESOLVED**: Dynamically imported Monaco editor component with custom loading skeleton. |
| **DEF-03** | Code Execution Sandbox | **BLOCKER** | Production environment could fall back to unisolated local `subprocess` runner | Missing production guard check in execution service | **RESOLVED**: Added strict `ENVIRONMENT=production` check raising `RuntimeError`. |
| **DEF-04** | Homepage Navigation | **HIGH** | Anchor hash links (`/#instructor`) changed URL but failed to scroll | Missing scroll margin offsets and client-side hash scroll handler | **RESOLVED**: Created `HashScrollHandler` component and added `scroll-margin-top` CSS rules. |
| **DEF-05** | Auth / RBAC | **CRITICAL**| Unauthenticated requests could attempt to access private lesson tokens | Missing dependency check on video playback token endpoint | **RESOLVED**: Added `get_current_user` dependency and active enrolment validation. |
