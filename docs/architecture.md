# Architecture Documentation - Code Journey Academy

## System Overview

Code Journey Academy is designed around a clean, modular full-stack architecture optimized for high-contrast Arabic RTL user experience, fast execution, security isolation, and reliable manual payment verification.

```
+-----------------------------------------------------------------------------------+
|                               Client Browser (RTL)                                |
|  Next.js 14 (App Router) | TypeScript | Tailwind CSS | Monaco Editor | React-Query   |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (Signed Cookies + JWT)
                                           v
+-----------------------------------------------------------------------------------+
|                              Nginx Reverse Proxy                                  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                               FastAPI Service Layer                               |
|  Security Middleware | Router Modules | Service Logic | SQLAlchemy 2.0 Async ORM |
+--------+------------------+-----------------------+---------------------+---------+
         |                  |                       |                     |
         v                  v                       v                     v
+----------------+ +----------------+  +--------------------+ +---------------------+
|   PostgreSQL   | |  Redis Cache   |  |   Judge0 Sandboxed | |  Cloudflare Stream  |
| Database (40+) | |   & Queue      |  |  Code Runner Engine| | Signed Token Video  |
+----------------+ +----------------+  +--------------------+ +---------------------+
```

## Layer Descriptions

1. **Frontend Presentation Layer**: Next.js 14 App Router with Tailwind CSS (`dir="rtl"` with Cairo typography). Uses `@monaco-editor/react` for student code playgrounds and `@tanstack/react-query` for state hydration.
2. **API & Security Gateways**: FastAPI REST API providing OpenAPI endpoints. Enforces Argon2id password hashing, HTTP-Only session cookies, CSRF protection, and RBAC authorization.
3. **Data Persistence**: PostgreSQL database using UUID primary keys, transactional integrity, soft-deletes where applicable, and indexed fields.
4. **Code Sandboxing Engine**: Judge0 integration via an abstract adapter interface, backed by a local subprocess mock runner enforcing process isolation, memory ceilings (128MB), and CPU time limits (2.0s).
5. **Video Protection Engine**: Private signed JWT playback tokens generated on demand for active students. Exposes no raw video stream links to the frontend.
