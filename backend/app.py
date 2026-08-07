import gradio as gr
from app.main import app as fastapi_app

demo = gr.Interface(
    fn=lambda name: f"Code Belaraby API Server is Online for {name}!",
    inputs="text",
    outputs="text",
    title="منصة كود بالعربي - API Server"
)

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
