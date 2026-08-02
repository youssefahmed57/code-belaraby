from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import User, VideoAsset, VideoProgress, LessonProgress
from app.api.deps import get_current_user
from app.services.video_service import get_video_playback_info
from app.services.unlock_service import evaluate_lesson_completion

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.get("/token/{video_id}")
async def get_signed_token(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    info = get_video_playback_info(video_id, current_user.id)
    return info

@router.get("/stream-mock/{video_id}", response_class=HTMLResponse)
async def stream_mock_video(
    video_id: str,
    token: str = Query(...)
):
    """
    Renders an HTML5 Video Player container with dynamic watermark overlay.
    """
    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
      <meta charset="utf-8">
      <style>
        body {{ margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; font-family: sans-serif; }}
        .video-container {{ position: relative; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; }}
        video {{ width: 100%; max-height: 100%; }}
        .watermark {{
          position: absolute;
          top: 20px;
          right: 20px;
          color: rgba(255,255,255,0.4);
          font-size: 14px;
          pointer-events: none;
          background: rgba(0,0,0,0.5);
          padding: 4px 10px;
          border-radius: 4px;
        }}
      </style>
    </head>
    <body>
      <div class="video-container">
        <div class="watermark">Code Journey Academy - Demo Stream</div>
        <video controls controlsList="nodownload">
          <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" type="video/mp4">
          متصفحك لا يدعم مشغل الفيديو.
        </video>
      </div>
    </body>
    </html>
    """

@router.post("/progress")
async def update_video_progress(
    lesson_id: str,
    video_id: str,
    current_position: float,
    duration: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if duration <= 0:
        pct = 0.0
    else:
        pct = min(round((current_position / duration) * 100.0, 2), 100.0)

    stmt_vp = select(VideoProgress).where(
        VideoProgress.student_id == current_user.id,
        VideoProgress.lesson_id == lesson_id,
        VideoProgress.video_asset_id == video_id
    )
    res_vp = await db.execute(stmt_vp)
    vp = res_vp.scalar_one_or_none()

    if not vp:
        vp = VideoProgress(
            student_id=current_user.id,
            lesson_id=lesson_id,
            video_asset_id=video_id,
            last_playback_position=current_position,
            completion_percentage=pct
        )
        db.add(vp)
    else:
        if pct > vp.completion_percentage:
            vp.completion_percentage = pct
        vp.last_playback_position = current_position
        if pct >= 80.0:
            vp.is_completed = True

    # Update Lesson Progress
    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == current_user.id,
        LessonProgress.lesson_id == lesson_id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()
    if lp:
        if pct > lp.video_watched_percentage:
            lp.video_watched_percentage = pct
        if pct >= 80.0:
            lp.video_completed = True

    await db.commit()

    is_completed, _ = await evaluate_lesson_completion(db, current_user.id, lesson_id)
    return {"watched_percentage": pct, "lesson_completed": is_completed}
