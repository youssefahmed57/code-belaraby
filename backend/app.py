import gradio as gr

try:
    from app.main import app as fastapi_app
    status_msg = "✅ FastAPI loaded successfully!"
except Exception as e:
    fastapi_app = None
    status_msg = f"❌ Error loading FastAPI: {str(e)}"

with gr.Blocks(title="Code Belaraby API") as demo:
    gr.Markdown("# 🚀 منصة كود بالعربي - Backend API Server")
    gr.Markdown(status_msg)

if fastapi_app is not None:
    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    demo.launch()
