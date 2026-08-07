import gradio as gr
from app.main import app as fastapi_app

with gr.Blocks(title="كود بالعربي - API Server") as demo:
    gr.Markdown("# 🚀 منصة كود بالعربي - Backend API Server")
    gr.Markdown("الخادم الخارجي يعمل بكفاءة تامة وتواصل مباشر مع واجهة Vercel/Netlify وقاعدة البيانات.")

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
