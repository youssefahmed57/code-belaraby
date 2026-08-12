import html
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.db.models import LessonProgress, User, VideoProgress
from app.services.access_service import require_accessible_video
from app.services.unlock_service import evaluate_lesson_completion
from app.services.video_service import (
    VideoProviderUnavailable,
    generate_student_code,
    get_video_playback_info,
    mask_phone_number,
)


router = APIRouter(prefix="/videos", tags=["Videos"])


class VideoProgressRequest(BaseModel):
    lesson_id: str
    video_id: str
    current_position: float = Field(..., ge=0)
    duration: float = Field(..., gt=0)


def _authoritative_duration_seconds(lesson, video_asset) -> float:
    if video_asset.duration_seconds and video_asset.duration_seconds > 0:
        return float(video_asset.duration_seconds)
    if lesson.estimated_duration_minutes and lesson.estimated_duration_minutes > 0:
        return float(lesson.estimated_duration_minutes * 60)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="تعذر تحديد مدة الفيديو بشكل موثوق.",
    )


def _compute_allowed_position(previous_position: float, previous_seen_at: datetime | None) -> float:
    if previous_seen_at is None:
        return previous_position + 30.0

    elapsed_seconds = max(0.0, (datetime.utcnow() - previous_seen_at).total_seconds())
    return previous_position + max(15.0, min(90.0, elapsed_seconds * 1.5 + 5.0))


@router.get("/token/{video_id}")
async def get_signed_token(
    video_id: str,
    lesson_id: str = Query(..., description="Lesson ID the video belongs to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    lesson, video_asset = await require_accessible_video(db, current_user.id, lesson_id, video_id)
    try:
        return await get_video_playback_info(
            video_asset=video_asset,
            student=current_user,
            lesson_id=lesson.id,
        )
    except VideoProviderUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="تعذر إنشاء تصريح مشاهدة الفيديو حالياً.",
        ) from exc


@router.get("/stream-mock/{video_id}", response_class=HTMLResponse)
async def stream_mock_video(
    video_id: str,
    lesson_id: str = Query(...),
    token: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.is_development_like():
        raise HTTPException(status_code=403, detail="مشغل الفيديو التجريبي غير متاح خارج بيئات التطوير والاختبار.")

    await require_accessible_video(db, current_user.id, lesson_id, video_id)
    student_name = html.escape(current_user.arabic_name or "طالب")
    student_code = generate_student_code(current_user.id)
    student_phone = mask_phone_number(current_user.phone_number or "")
    watermark_text = f"🔒 {student_name} • {student_code} • {student_phone} • كود بالعربي"

    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
      <meta charset="utf-8">
      <title>كود بالعربي - مشغل الدرس المحمي</title>
      <style>
        body {{ margin: 0; background: #0b0f19; color: white; font-family: system-ui, sans-serif; }}
        .video-container {{ position: relative; width: 100vw; height: 100vh; background: #000; }}
        video {{ width: 100%; height: 100%; object-fit: contain; }}
        .watermark {{ position: absolute; top: 15%; right: 15%; color: rgba(255, 255, 255, 0.55); font-size: 12px; font-weight: 700; pointer-events: none; background: rgba(15, 23, 42, 0.7); padding: 6px 14px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.15); backdrop-filter: blur(4px); z-index: 99; white-space: nowrap; }}
        .security-badge {{ position: absolute; bottom: 12px; right: 12px; background: rgba(15, 23, 42, 0.85); color: #38bdf8; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.25); pointer-events: none; z-index: 100; }}
      </style>
    </head>
    <body oncontextmenu="return false;" ondragstart="return false;">
      <div id="videoWrap" class="video-container">
        <div id="dynamicWatermark" class="watermark">{watermark_text}</div>
        <div class="security-badge">Dev/Test Mock Player</div>
        <video id="mainVideo" controls controlsList="nodownload noplaybackrate" disablePictureInPicture>
          <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" type="video/mp4">
        </video>
      </div>
      <script>
        const lessonId = {lesson_id!r};
        const videoId = {video_id!r};
        const token = {token!r};
        const wm = document.getElementById("dynamicWatermark");
        const video = document.getElementById("mainVideo");
        const wrap = document.getElementById("videoWrap");
        const positions = [
          {{ top: "10%", right: "10%" }},
          {{ top: "70%", right: "15%" }},
          {{ top: "25%", right: "60%" }},
          {{ top: "65%", right: "55%" }},
          {{ top: "40%", right: "20%" }},
          {{ top: "15%", right: "50%" }}
        ];
        let idx = 0;
        let lastSentAt = 0;
        function postProgress() {{
          if (!video || !video.duration || !window.parent) return;
          const now = Date.now();
          if (now - lastSentAt < 5000) return;
          lastSentAt = now;
          window.parent.postMessage({{
            type: "lesson-video-progress",
            lessonId,
            videoId,
            currentPosition: video.currentTime,
            duration: video.duration,
            token
          }}, "*");
        }}
        ["timeupdate", "pause", "ended"].forEach((eventName) => {{
          video.addEventListener(eventName, postProgress);
        }});
        setInterval(() => {{
          idx = (idx + 1) % positions.length;
          wm.style.top = positions[idx].top;
          wm.style.right = positions[idx].right;
          wm.style.opacity = Math.random() > 0.5 ? "0.6" : "0.35";
        }}, 6000);
        new MutationObserver(() => {{
          const checkWm = document.getElementById("dynamicWatermark");
          if (!checkWm || checkWm.style.display === "none" || checkWm.style.visibility === "hidden" || checkWm.style.opacity === "0") {{
            if (video) video.pause();
            alert("تم رصد محاولة العبث بالعلامة المائية.");
            location.reload();
          }}
        }}).observe(wrap, {{ childList: true, subtree: true, attributes: true }});
      </script>
    </body>
    </html>
    """


@router.post("/progress")
async def update_video_progress(
    req: VideoProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lesson, video_asset = await require_accessible_video(db, current_user.id, req.lesson_id, req.video_id)
    authoritative_duration = _authoritative_duration_seconds(lesson, video_asset)

    if req.current_position > authoritative_duration:
        raise HTTPException(status_code=400, detail="موضع التشغيل أكبر من مدة الفيديو الفعلية.")

    video_progress = await db.scalar(
        select(VideoProgress).where(
            VideoProgress.student_id == current_user.id,
            VideoProgress.lesson_id == lesson.id,
            VideoProgress.video_asset_id == video_asset.id,
        )
    )

    if not video_progress:
        if req.current_position > min(30.0, authoritative_duration * 0.2):
            raise HTTPException(status_code=400, detail="تم رفض قفزة مشاهدة غير منطقية في أول تحديث.")
        video_progress = VideoProgress(
            student_id=current_user.id,
            lesson_id=lesson.id,
            video_asset_id=video_asset.id,
            last_playback_position=req.current_position,
            total_watched_seconds=min(authoritative_duration, req.current_position),
            completion_percentage=round((req.current_position / authoritative_duration) * 100.0, 2),
        )
        db.add(video_progress)
    else:
        previous_position = max(0.0, video_progress.last_playback_position or 0.0)
        allowed_position = _compute_allowed_position(previous_position, video_progress.last_watched_at)
        if req.current_position > allowed_position:
            raise HTTPException(status_code=400, detail="تم رفض قفزة مشاهدة غير منطقية.")

        incremental_watch = 0.0
        if req.current_position >= previous_position:
            incremental_watch = req.current_position - previous_position
        video_progress.total_watched_seconds = min(
            authoritative_duration,
            max(video_progress.total_watched_seconds or 0.0, 0.0) + incremental_watch,
        )
        video_progress.last_playback_position = req.current_position
        video_progress.last_watched_at = datetime.utcnow()
        video_progress.completion_percentage = round(
            min(100.0, (video_progress.total_watched_seconds / authoritative_duration) * 100.0),
            2,
        )
        if req.current_position < previous_position:
            video_progress.session_count = max(1, (video_progress.session_count or 1) + 1)

    if video_progress.completion_percentage >= lesson.required_video_percentage:
        video_progress.is_completed = True
        video_progress.completed_at = video_progress.completed_at or datetime.utcnow()

    lesson_progress = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if not lesson_progress:
        lesson_progress = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lesson_progress)

    lesson_progress.video_watched_percentage = max(
        lesson_progress.video_watched_percentage or 0.0,
        video_progress.completion_percentage,
    )
    if video_progress.completion_percentage >= lesson.required_video_percentage:
        lesson_progress.video_completed = True

    await db.commit()

    lesson_completed, _ = await evaluate_lesson_completion(db, current_user.id, lesson.id)
    return {
        "watched_percentage": video_progress.completion_percentage,
        "lesson_completed": lesson_completed,
    }
