import os
import gradio as gr

def get_sys_status():
    secret_set = "SECRET_KEY" in os.environ
    db_set = "DATABASE_URL" in os.environ
    return f"Status: Secret={secret_set}, DB={db_set}"

with gr.Blocks(title="Code Belaraby API") as demo:
    gr.Markdown("# 🚀 منصة كود بالعربي - Live API Server")
    gr.Markdown("السيرفر يعمل الآن بنجاح على منصة Hugging Face.")
    btn = gr.Button("فحص حالة البيئة")
    out = gr.Textbox(label="حالة متغيرات البيئة")
    btn.click(fn=get_sys_status, inputs=[], outputs=[out])

try:
    from app.main import app as fastapi_app
    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
except Exception as e:
    print(f"FastAPI import error: {e}")

if __name__ == "__main__":
    demo.launch()
