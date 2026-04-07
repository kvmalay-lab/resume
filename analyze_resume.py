import google.generativeai as genai
import os
import re

# 1. FIX THE 404: Use the updated model naming and API version
# Ensure your API key is set in your environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"))

def analyze_resume(resume_text, target_job="Senior Software Engineer / Full-Stack Developer"):
    # Initialize the model correctly to avoid 404 models/gemini-pro
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro',
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }
    )
    
    # Strip unusual formatting characters (keep basic whitespace and alphanumeric/punctuation)
    # This helps the model focus on content rather than fixing formatting
    clean_resume_text = re.sub(r'[^\w\s\.,;:!\?\'\"\(\)\[\]\{\}\-\+\=\@\#\$\%\^\&\*\/\|\\]', '', resume_text)

    # The Master Prompt (De-AI'd and UI-focused)
    prompt = f"""
    ROLE: Senior Technical Recruiter & Resume Strategist.
    CONTEXT: Analyze this resume for a {target_job} role. 
    
    CRITICAL INSTRUCTION: Do not use generic AI greetings. Use a direct, 
    editorial tone. Avoid phrases like "it's important to note." 
    Focus on high-signal evidence.

    UI STRUCTURE:
    # STRATEGY REPORT: {target_job}
    ---
    ## ⚡ THE 6-SECOND SCAN
    [Provide a blunt assessment of what a recruiter sees in the first 6 seconds]

    ## 🚩 HARD TRUTHS (WHAT TO CUT)
    * [Point 1: Mention specific fluff or outdated tech]
    * [Point 2: Mention weak verbs or passive impact]

    ## 🛠️ HIGH-IMPACT REWRITES
    | Before (Weak) | After (Strong/Quantified) | Rationale |
    | :--- | :--- | :--- |
    | [Point 1] | [Rewrite 1] | [Why it works] |
    | [Point 2] | [Rewrite 2] | [Why it works] |

    ## 🔍 THE EVIDENCE GAP
    [Identify 2-3 specific 2026 industry trends or skills missing from this resume.]

    ---
    RESUME TEXT:
    {clean_resume_text}
    """

    response = model.generate_content(prompt)
    return response.text

# Usage
if __name__ == "__main__":
    sample_resume = "Your resume text here..."
    result = analyze_resume(sample_resume)
    print(result)
