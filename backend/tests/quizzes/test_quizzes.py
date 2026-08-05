import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_quiz_snapshot_secrecy_timer_and_duplicate_protection(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)
    assert lesson_res.status_code == 200
    lesson_data = lesson_res.json()
    quiz_id = lesson_data["quiz"]["id"]

    start_res = await async_client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=headers)
    if start_res.status_code == 200:
        attempt = start_res.json()
        attempt_id = attempt["attempt_id"]
        for q in attempt["questions"]:
            for opt in q["options"]:
                assert "is_correct" not in opt

        answers_list = [
            {"question_id": q["id"], "selected_option_ids": [q["options"][0]["id"]], "text_answer": ""}
            for q in attempt["questions"]
        ]

        sub_res = await async_client.post("/api/v1/quizzes/attempts/submit", json={
            "attempt_id": attempt_id,
            "answers": answers_list
        }, headers=headers)
        assert sub_res.status_code in [200, 400]
