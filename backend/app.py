import gradio as gr
import uvicorn
from app.main import app as fastapi_app

demo = gr.Interface(
    fn=lambda name: f"Hello {name}, Code Belaraby FastAPI is Online!",
    inputs="text",
    outputs="text",
    title="Code Belaraby API"
)

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
