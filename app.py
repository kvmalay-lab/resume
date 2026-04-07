import gradio as gr
import json
import os
import io
from dotenv import load_dotenv

load_dotenv()

from agents import ResumeAnalyzerAgent, ImprovementAgent
from tools import extract_text, export_to_pdf, export_to_docx
from memory import SessionMemory

analyzer = ResumeAnalyzerAgent()
improver = ImprovementAgent()

# Custom CSS for Deep Dark Mode & Neon Accents
custom_css = """
body, .gradio-container {
    background-color: #0b0c10 !important;
    color: #c5c6c7 !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}
.gr-box, .gr-panel, .gr-input, .gr-textarea {
    background-color: #1f2833 !important;
    border: 1px solid #45a29e !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
.gr-button.primary {
    background: linear-gradient(90deg, #66fcf1 0%, #45a29e 100%) !important;
    border: none !important;
    color: #0b0c10 !important;
    font-weight: 800 !important;
    box-shadow: 0 0 10px rgba(102, 252, 241, 0.4) !important;
    transition: all 0.3s ease !important;
}
.gr-button.primary:hover {
    box-shadow: 0 0 20px rgba(102, 252, 241, 0.8) !important;
    transform: translateY(-2px);
}
.gr-button.secondary {
    background-color: transparent !important;
    border: 2px solid #66fcf1 !important;
    color: #66fcf1 !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.gr-button.secondary:hover {
    background-color: #66fcf1 !important;
    color: #0b0c10 !important;
}
h1, h2, h3 {
    color: #66fcf1 !important;
    text-shadow: 0 0 8px rgba(102, 252, 241, 0.4) !important;
    font-weight: bold;
}
.analysis-box {
    padding: 20px;
    border-radius: 10px;
    background-color: #1f2833;
    border-left: 5px solid #ff0055;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    margin-top: 15px;
    font-size: 0.95em;
    line-height: 1.5em;
}
.analysis-score {
    font-size: 2.2em;
    font-weight: 900;
    color: #ff0055;
    text-shadow: 0 0 15px rgba(255, 0, 85, 0.6);
    margin-bottom: 10px;
}
#original_view > label > textarea, #improved_view > label > textarea {
    height: 500px !important;
    font-family: 'Consolas', monospace !important;
    font-size: 0.9em;
    background-color: #0b0c10 !important;
    border: 1px solid #45a29e !important;
}
.chatbot-message {
    border-radius: 8px !important;
}
"""

def process_upload(file_obj, session_state):
    if file_obj is None:
        return "No file uploaded.", session_state, gr.update()
    
    text = extract_text(file_obj.name)
    if "Error" in text:
        return text, session_state, gr.update()
    
    session_state.clear() # Reset on new upload
    session_state.set_original_resume(text)
    return text, session_state, gr.update(value="<div style='color:#66fcf1; font-weight:bold;'>File loaded successfully. Click 'Analyze & Improve'</div>")

def analyze_and_improve(session_state):
    if not session_state.original_resume:
         return session_state.original_resume, "Please upload a resume first.", session_state, "<div class='analysis-box'>No analysis available</div>"
    
    # Analyze
    analysis = analyzer.analyze_resume(session_state.original_resume)
    if "error" in analysis:
        return session_state.original_resume, f"Error: {analysis['error']}", session_state, f"<div class='analysis-box'>Analysis failed: {analysis['error']}</div>"
    
    session_state.set_analysis(analysis)
    
    # Improve
    improved_text = improver.suggest_improvements(session_state.original_resume, analysis)
    if "Error" in improved_text:
        return session_state.original_resume, improved_text, session_state, "<div class='analysis-box'>Improvement failed.</div>"
        
    session_state.update_resume(improved_text, feedback="Initial AI optimization based on analysis.")
    
    score = analysis.get('score', 0)
    strengths = "<br>- ".join(analysis.get('strengths', []))
    if strengths: strengths = "- " + strengths
    weaknesses = "<br>- ".join(analysis.get('weaknesses', []))
    if weaknesses: weaknesses = "- " + weaknesses
    missing = "<br>- ".join(analysis.get('missing_keywords', []))
    if missing: missing = "- " + missing

    HTML_context = f"<div class='analysis-box'>" \
                   f"<div class='analysis-score'>Score: {score}/100</div>" \
                   f"<b style='color:#66fcf1'>Strengths:</b><br>{strengths}<br><br>" \
                   f"<b style='color:#ff0055'>Weaknesses:</b><br>{weaknesses}<br><br>" \
                   f"<b style='color:#ff0055'>Missing Keywords:</b><br>{missing}" \
                   f"</div>"
                   
    return session_state.original_resume, session_state.current_resume, session_state, HTML_context

def handle_chat(user_message, session_state, chatbot):
    if not session_state.current_resume:
        chatbot.append((user_message, "Please process a resume first before chatting."))
        return "", chatbot, session_state, session_state.current_resume
    
    session_state.add_message("user", user_message)
    chatbot.append((user_message, None))
    
    new_resume = improver.chat_rewrite(
         current_resume=session_state.current_resume,
         chat_history=session_state.chat_history,
         new_request=user_message
    )
    
    if "Error" in new_resume:
       fallback_msg = "Sorry, I encountered an error modifying the resume."
       session_state.add_message("assistant", fallback_msg)
       chatbot[-1] = (user_message, fallback_msg)
       return "", chatbot, session_state, session_state.current_resume
       
    session_state.update_resume(new_resume, feedback=user_message)
    success_msg = "I have updated the resume perfectly based on your feedback. Please check the 'Improved Resume' view."
    session_state.add_message("assistant", success_msg)
    
    chatbot[-1] = (user_message, success_msg)
    
    return "", chatbot, session_state, session_state.current_resume

def export_files(session_state):
    if not session_state.current_resume:
        return None
        
    pdf_path = f"improved_resume_{session_state.session_id}.pdf"
    docx_path = f"improved_resume_{session_state.session_id}.docx"
    export_to_pdf(session_state.current_resume, pdf_path)
    export_to_docx(session_state.current_resume, docx_path)
    
    outputs = []
    if os.path.exists(pdf_path): outputs.append(pdf_path)
    if os.path.exists(docx_path): outputs.append(docx_path)
    
    return outputs

with gr.Blocks(css=custom_css, title="AI Resume Reviewer & Improver", theme=gr.themes.Base()) as app:
    session_state = gr.State(SessionMemory())
    
    with gr.Row():
        gr.Markdown("# 🚀 AI Resume Reviewer & Improver\nUpload your resume, see instant AI analysis, and iteratively perfect your bullet points.")
    
    with gr.Row():
         with gr.Column(scale=1):
             upload_comp = gr.File(label="Upload Resume (PDF, DOCX, TXT)", file_types=[".pdf", ".docx", ".txt"])
             status_msg = gr.HTML("<div style='color:#a0a0a0'>Waiting for upload...</div>")
             analyze_btn = gr.Button("⚡ Analyze & Improve", variant="primary")
             
             with gr.Accordion("Analysis Results", open=True):
                 analysis_output = gr.HTML("<div class='analysis-box'>Upload a resume to see analysis.</div>")
                 
         with gr.Column(scale=2):
             with gr.Row():
                 original_view = gr.TextArea(label="Original Resume", interactive=True, elem_id="original_view")
                 improved_view = gr.TextArea(label="Improved Resume", interactive=True, elem_id="improved_view")
             
             with gr.Row():
                 export_btn = gr.Button("💾 Download PDF & DOCX", variant="secondary")
                 download_files = gr.File(label="Exported Files")
             
             gr.Markdown("### 💬 Interactive Improvement Chat\nChat with the agent to refine specific sections.")
             chatbot = gr.Chatbot(label="Improver Agent", height=200)
             chat_input = gr.Textbox(placeholder="E.g., 'Make the experience section sound more leadership-focused'...", label="Your instructions")

    # Wire up events
    upload_comp.upload(
         fn=process_upload, 
         inputs=[upload_comp, session_state], 
         outputs=[original_view, session_state, status_msg]
    )
    
    analyze_btn.click(
         fn=analyze_and_improve,
         inputs=[session_state],
         outputs=[original_view, improved_view, session_state, analysis_output]
    )
    
    chat_input.submit(
         fn=handle_chat,
         inputs=[chat_input, session_state, chatbot],
         outputs=[chat_input, chatbot, session_state, improved_view]
    )
    
    export_btn.click(
         fn=export_files,
         inputs=[session_state],
         outputs=[download_files]
    )

if __name__ == "__main__":
    app.launch()
