import random
from locust import HttpUser, task, between

class StudentUser(HttpUser):
    wait_time = between(1, 4)
    token = None
    headers = {}

    def on_start(self):
        """Simulate student login upon starting a session"""
        # Login with seed student account or random student identifier
        resp = self.client.post("/api/v1/auth/login", json={
            "identifier": "01011111111",
            "password": "StudentPass123!@#"
        })
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(4)
    def view_dashboard_and_courses(self):
        """Task 1: Open dashboard and list courses"""
        self.client.get("/api/v1/dashboard/summary", headers=self.headers, name="/api/v1/dashboard/summary")
        self.client.get("/api/v1/courses", headers=self.headers, name="/api/v1/courses")

    @task(3)
    def view_lesson_details(self):
        """Task 2: Student opens a lesson and watches video"""
        lesson_id = "demo_lesson_1"
        self.client.get(f"/api/v1/lessons/{lesson_id}", headers=self.headers, name="/api/v1/lessons/[id]")
        
        # Simulate video progress heartbeat (every few seconds)
        self.client.post("/api/v1/lessons/progress", json={
            "lesson_id": lesson_id,
            "seconds_watched": random.randint(10, 120),
            "completed": False
        }, headers=self.headers, name="/api/v1/lessons/progress")

    @task(2)
    def execute_code_playground(self):
        """Task 3: Student writes code in Monaco Editor and submits for execution"""
        code_samples = [
            "print('Hello Code Belaraby!')",
            "x = sum([i for i in range(100)])\nprint(f'Total: {x}')",
            "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\nprint(factorial(5))"
        ]
        self.client.post("/api/v1/coding-problems/run", json={
            "language": "python",
            "source_code": random.choice(code_samples),
            "stdin": ""
        }, headers=self.headers, name="/api/v1/coding-problems/run")

    @task(1)
    def submit_quiz_attempt(self):
        """Task 4: Student completes a quiz and submits answers"""
        self.client.post("/api/v1/quizzes/demo_quiz_1/submit", json={
            "answers": {
                "q1": "opt_a",
                "q2": "opt_b"
            }
        }, headers=self.headers, name="/api/v1/quizzes/[id]/submit")

    @task(1)
    def check_detailed_health(self):
        """Task 5: Probe system health endpoint"""
        self.client.get("/api/v1/health/detailed", name="/api/v1/health/detailed")
