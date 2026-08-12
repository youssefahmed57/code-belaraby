# 📦 01. Repository Inventory & Discovery Report

> Historical snapshot from Saturday, August 2, 2026. This file is not the current deployment authority and may describe pre-hardening behavior. For the active production/staging design, use `docs/deployment-architecture.md`.

**Audit Date**: 2026-08-02  
**Branch**: `production-readiness-audit`  
**Auditor**: Senior Production Readiness & Full-Stack Security Auditor  

---

## 1. Applications and Services

| Application / Service | Technology Stack | Location | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | Next.js 14.2.35 (App Router), React 18, TailwindCSS, Monaco Editor | `frontend/` | Active (14 Static/Dynamic routes) |
| **Backend API Service** | FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, Uvicorn | `backend/` | Active |
| **Relational Database** | PostgreSQL 15 / SQLite (Dev fallback) | `backend/app/db` | Active |
| **Cache & Session Store** | Redis 7 (Alpine) | Docker Compose | Configured |
| **Reverse Proxy** | Nginx Alpine | `nginx/default.conf` | Configured |
| **Code Execution Engine** | Local Subprocess Fallback / Judge0 API Adapter | `backend/app/services/execution_service.py` | Local Active / Judge0 Mocked |
| **Video Streaming** | Cloudflare Stream API Adapter | `backend/app/services/video_service.py` | Mocked / Pending Credentials |
| **Storage Engine** | Local Disk (`./uploads`) / Cloudflare R2 S3 Adapter | `backend/app/services/storage_service.py` | Local Active |
| **Automation & Workflows**| n8n Outbox Webhook Dispatcher | `backend/app/services/n8n_service.py` | Outbox Schema / Pending Instance |

---

## 2. Frontend Route Inventory (`frontend/src/app`)

| Route Path | Type | Purpose | Auth Requirement |
| :--- | :--- | :--- | :--- |
| `/` | Static (Page) | Homepage (Hero, Instructor, Pricing, How it works, FAQ, Contact) | Public |
| `/courses` | Static (Page) | Public Course Catalog | Public |
| `/courses/[slug]` | Dynamic (Page) | Public Course Details & Curriculum | Public |
| `/login` | Static (Page) | Student & Admin Login Form | Public |
| `/register` | Static (Page) | Egyptian Phone Registration Form | Public |
| `/terms` | Static (Page) | Terms of Service Policy | Public |
| `/privacy` | Static (Page) | Privacy Policy | Public |
| `/refund` | Static (Page) | Refund Policy | Public |
| `/dashboard` | Static (Page) | Student Dashboard (Enrolments, Progress, Action CTAs) | Student (Protected) |
| `/dashboard/lessons/[id]`| Dynamic (Page) | Lesson Workspace (Video, Theory, Quiz, Practical Challenge) | Student (Enrolled) |
| `/dashboard/payments` | Static (Page) | Payment Order History & Receipt Upload | Student (Protected) |
| `/dashboard/playground` | Static (Page) | Standalone Monaco Code Playground | Student (Protected) |
| `/admin` | Static (Page) | Admin Dashboard (Metrics, Payment Review, CSV Exports) | Admin / Super Admin |

---

## 3. Backend API Route Inventory (`backend/app/api/v1`)

| Endpoint Path | HTTP Method | Handler Function | Security / RBAC |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth/register` | `POST` | `register` | Public |
| `/api/v1/auth/login` | `POST` | `login` | Public |
| `/api/v1/auth/logout` | `POST` | `logout` | Authenticated |
| `/api/v1/courses` | `GET` | `list_courses` | Public |
| `/api/v1/courses/{slug}` | `GET` | `get_course_details` | Public |
| `/api/v1/payments/order` | `POST` | `request_payment` | Student |
| `/api/v1/payments/upload-receipt` | `POST` | `upload_receipt` | Student |
| `/api/v1/payments/my-payments` | `GET` | `get_my_payments` | Student |
| `/api/v1/payments/admin/pending` | `GET` | `get_pending_payments` | Admin |
| `/api/v1/payments/admin/review` | `POST` | `admin_review_payment` | Admin |
| `/api/v1/lessons/{id}` | `GET` | `get_lesson_details` | Student (Enrolled) |
| `/api/v1/lessons/{id}/progress` | `POST` | `update_lesson_progress` | Student (Enrolled) |
| `/api/v1/quizzes/{id}/start` | `POST` | `start_quiz` | Student (Enrolled) |
| `/api/v1/quizzes/attempts/submit`| `POST` | `submit_quiz` | Student (Enrolled) |
| `/api/v1/coding-problems/run` | `POST` | `run_playground_code` | Student |
| `/api/v1/coding-problems/submit` | `POST` | `submit_problem_solution` | Student (Enrolled) |
| `/api/v1/admin/metrics` | `GET` | `get_admin_metrics` | Admin |
| `/api/v1/admin/export/students` | `GET` | `export_students_csv` | Admin |
| `/api/v1/admin/export/payments` | `GET` | `export_payments_csv` | Admin |
| `/api/v1/videos/token/{id}` | `GET` | `get_video_playback_token` | Student (Enrolled) |

---

## 4. Database Models & Alembic Migrations

### Models (`backend/app/db/models.py`):
- `User` (id, arabic_name, phone_number, password_hash, role, grade_level, is_active, created_at)
- `UserSession` (id, user_id, session_token, ip_address, user_agent, expires_at)
- `Course` (id, title, slug, description, grade_level, price, instructor_name, is_published, status, visibility)
- `Module` (id, course_id, title, order)
- `Lesson` (id, module_id, title, slug, summary, video_url, theory_content, order, is_preview)
- `Payment` (id, student_id, course_id, amount_paid, status, payment_method, receipt_url, transaction_reference, reviewed_at, reviewer_id)
- `Enrolment` (id, student_id, course_id, is_active, access_start, access_expiry)
- `LessonProgress` (id, student_id, lesson_id, video_watched_percentage, theory_completed, quiz_passed, practical_submitted, practical_passed, is_completed)
- `Quiz` (id, lesson_id, title, time_limit_minutes, passing_score, allowed_attempts)
- `Question` (id, quiz_id, question_text, question_type, points, order)
- `QuestionOption` (id, question_id, option_text, is_correct)
- `QuizAttempt` (id, student_id, quiz_id, score, passed, started_at, completed_at)
- `CodingProblem` (id, lesson_id, title, description, starter_code, time_limit_seconds)
- `TestCase` (id, problem_id, input_data, expected_output, is_public, order)
- `CodeSubmission` (id, student_id, problem_id, lesson_id, language, source_code, status, score)
- `SubmissionTestResult` (id, submission_id, test_case_id, is_passed, status, stdout, stderr)
- `AuditLog` (id, user_id, action, entity_type, entity_id, details, ip_address, timestamp)
- `OutboxEvent` (id, event_type, payload, status, retry_count, created_at)

### Alembic Migrations (`backend/alembic/versions`):
- `001_initial_schema.py` (Base migration covering all 18 models)

---

## 5. Mocked Components & Integration Dependencies

1. **Judge0 API Adapter**:
   - `USE_MOCK_JUDGE0=true` in `.env`. Local execution is fallback for dev, but prohibited when `ENVIRONMENT=production`.
2. **Cloudflare Stream Video Adapter**:
   - `USE_MOCK_VIDEO_PROVIDER=true` in `.env`. Returns signed mock tokens for demo video IDs.
3. **Storage Engine**:
   - `STORAGE_PROVIDER=local`. Local disk uploads stored in `./uploads`.
4. **n8n Automation Engine**:
   - Outbox event table exists in database schema; external n8n engine instance is pending deployment/credentials.

---

## 6. Code Findings & Risk Analysis

| Search Term | Findings / Locations | Classification |
| :--- | :--- | :--- |
| `TODO / FIXME` | Clean (0 active TODO/FIXME markers in core code) | BENIGN |
| `mock` | `USE_MOCK_JUDGE0=true`, `USE_MOCK_VIDEO_PROVIDER=true` in `.env` | PENDING CREDENTIALS |
| `fake` | Clean in production logic | BENIGN |
| `hardcoded` | Clean in production logic | BENIGN |
| `localhost / 127.0.0.1` | `.env` and `config.py` default fallbacks | DEVELOPMENT DEFAULTS |
| `AdminPass / StudentPass` | Seed script test accounts (`app/db/seed.py`) | DEV SEED DATA |
| `secret` | `JWT_SECRET_KEY`, `CSRF_SECRET` in `.env` | SECRET (Needs Production Rotation) |
| `is_correct` | Hidden in network responses (`start_quiz` strips `is_correct`) | VERIFIED SECURE |
| `subprocess` | `ExecutionService.run_code_sync` local fallback | HIGH (Must block in PROD) |
| `create_all` | Used only in fallback scripts; Alembic is primary | VERIFIED |

---

## 7. Current Test Suite Status

- **Backend Pytest**: `14/14 Passed` (`python -m pytest tests/test_backend.py`)
- **Frontend TypeScript**: `0 Errors` (`npx tsc --noEmit`)
- **Frontend Production Build**: `Passed` (`npm run build`, 14 pages generated)
- **Playwright E2E Suite**: `27/27 Passed` (`npx playwright test`)
