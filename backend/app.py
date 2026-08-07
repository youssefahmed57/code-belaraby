import gradio as gr

def greet(name):
    return f"Hello {name}, Code Belaraby Space is Live with 16GB RAM!"

demo = gr.Interface(
    fn=greet,
    inputs="text",
    outputs="text",
    title="منصة كود بالعربي - Live API Server"
)

if __name__ == "__main__":
    demo.launch()
