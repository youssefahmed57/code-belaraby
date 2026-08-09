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
    token: str = Query(...),
    student_name: str = Query(default="طالب كود بالعربي"),
    student_phone: str = Query(default="Code Belaraby Student")
):
    """
    Renders a secure HTML5 Video Player container with dynamic moving watermark overlay and nodownload protection.
    """
    return f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
      <meta charset="utf-8">
      <title>كود بالعربي - مشغل الدرس المحمي</title>
      <style>
        body {{ margin: 0; background: #0b0f19; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; font-family: system-ui, -apple-system, sans-serif; user-select: none; -webkit-user-select: none; }}
        .video-container {{ position: relative; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: #000; overflow: hidden; }}
        video {{ width: 100%; height: 100%; object-fit: contain; }}
        .watermark {{
          position: absolute;
          top: 15%;
          right: 15%;
          color: rgba(255, 255, 255, 0.45);
          font-size: 13px;
          font-weight: 700;
          pointer-events: none;
          background: rgba(15, 23, 42, 0.65);
          padding: 6px 14px;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(4px);
          transition: all 1.2s ease-in-out;
          z-index: 99;
          letter-spacing: 0.5px;
        }}
        .security-badge {{
          position: absolute;
          bottom: 12px;
          right: 12px;
          background: rgba(15, 23, 42, 0.8);
          color: #38bdf8;
          font-size: 10px;
          font-weight: bold;
          padding: 4px 8px;
          border-radius: 8px;
          border: 1px solid rgba(56, 189, 248, 0.2);
          pointer-events: none;
          z-index: 100;
        }}
      </style>
    </head>
    <body oncontextmenu="return false;" ondragstart="return false;">
      <div class="video-container">
        <div id="dynamicWatermark" class="watermark">
          🔒 {student_name} ({student_phone}) • كود بالعربي
        </div>
        <div class="security-badge">
          🛡️ مشغل محمي بـ HLS & Dynamic Watermark
        </div>
        <video controls controlsList="nodownload noplaybackrate" disablePictureInPicture oncontextmenu="return false;">
          <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" type="video/mp4">
          متصفحك لا يدعم مشغل الفيديو.
        </video>
      </div>

      <script>
        // Dynamic Floating Watermark Positioning Engine
        const wm = document.getElementById("dynamicWatermark");
        const positions = [
          {{ top: '10%', right: '10%' }},
          {{ top: '70%', right: '15%' }},
          {{ top: '25%', right: '60%' }},
          {{ top: '65%', right: '55%' }},
          {{ top: '40%', right: '20%' }},
          {{ top: '15%', right: '50%' }}
        ];
        let idx = 0;
        setInterval(() => {{
          idx = (idx + 1) % positions.length;
          wm.style.top = positions[idx].top;
          wm.style.right = positions[idx].right;
          wm.style.opacity = Math.random() > 0.5 ? "0.6" : "0.35";
        }}, 6000);
      </script>
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
