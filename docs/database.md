# Database & ERD Documentation - Code Journey Academy

## Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : contains
    ROLES ||--o{ ROLE_PERMISSIONS : grants
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : includes
    USERS ||--o{ ENROLMENTS : registers
    COURSES ||--o{ ENROLMENTS : contains
    COURSES ||--o{ MODULES : includes
    MODULES ||--o{ LESSONS : includes
    LESSONS ||--o{ QUIZZES : has
    LESSONS ||--o{ CODING_PROBLEMS : contains
    USERS ||--o{ PAYMENTS : submits
    PAYMENTS ||--o{ PAYMENT_EVENTS : logs
    QUIZZES ||--o{ QUIZ_ATTEMPTS : attempts
    CODING_PROBLEMS ||--o{ CODE_SUBMISSIONS : submits
```

## Database Schema Structure

The platform uses over 35 core normalized tables in PostgreSQL:

1. `users`: Stores student and staff accounts (UUID, arabic_name, phone_number, email, hashed_password, grade_level, status).
2. `roles` & `permissions`: Role-Based Access Control matrix.
3. `courses`, `modules`, `lessons`: Curriculum structure with prerequisites and unlock parameters.
4. `payments` & `payment_events`: Manual payment receipts, reference numbers, InstaPay identifiers, and review drawer audit trails.
5. `enrolments`: Course access records with access start and expiry timestamps.
6. `quizzes`, `questions`, `quiz_attempts`: Server-controlled timed assessments with randomized options and attempt snapshotting.
7. `coding_problems`, `test_cases`, `code_submissions`: Practical challenge statements, hidden/public test cases, and execution run logs.
8. `lesson_progress`, `video_progress`, `course_progress`: Granular tracking of video watch %, theory completion, practical submissions, and quiz scores.
9. `platform_settings`: Dynamic branding (instructor name, contacts, colors, passing scores).
