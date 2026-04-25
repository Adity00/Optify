import gradio as gr

def demo_interface():
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        gr.Markdown("# ⚔️ CodeForge RL Arena")
        gr.Markdown("Watch the GRPO-trained agent optimize and fix code in real-time.")
        
        with gr.Row():
            with gr.Column():
                input_code = gr.Code(label="Input Code", language="python")
                task_dropdown = gr.Dropdown(choices=["Fix Bug", "Optimize", "Refactor"], label="Task Type")
                run_btn = gr.Button("Forge Code", variant="primary")
                
            with gr.Column():
                output_code = gr.Code(label="Forged Code", language="python")
                
        with gr.Row():
            cc_score = gr.Number(label="Cyclomatic Complexity Change")
            loc_score = gr.Number(label="LOC Change")
            
        def mock_forge(code, task):
            return code + "\n# Optimized by CodeForge", -2.5, -10
            
        run_btn.click(fn=mock_forge, inputs=[input_code, task_dropdown], outputs=[output_code, cc_score, loc_score])
        
    return app

if __name__ == "__main__":
    demo_interface().launch()
