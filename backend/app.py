import gradio as gr
import uvicorn
from app.main import app as fastapi_app

demo = gr.Interface(
    fn=lambda: "Code Belaraby FastAPI Server is Online with 16GB RAM!",
    inputs=[],
    outputs="text",
    title="كود بالعربي - API Server"
)

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=7860)
