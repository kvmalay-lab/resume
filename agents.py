import os
import json
from google import genai
from typing import List, Dict, Any

class ResumeAnalyzerAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.is_configured = True
            self.model = "gemini-2.5-flash"  # Using newest stable text model
        else:
            self.client = None
            self.is_configured = False

    def analyze_resume(self, text: str) -> Dict[str, Any]:
        """
        Parses and evaluates resume content against industry standards.
        Returns a structured dictionary with analysis.
        """
        if not self.is_configured:
            return {"error": "Gemini API key not configured. Set GEMINI_API_KEY in your env variables."}
        
        system_prompt = (
            "You are an expert HR Manager and Resume Evaluator. Analyze the provided resume text. "
            "Identify formatting issues, weak action verbs, missing industry standard keywords, and overall impact. "
            "Output the results strictly as a JSON object with the following keys: "
            "'score' (number between 0 and 100), 'strengths' (list of strings), 'weaknesses' (list of strings), "
            "'missing_keywords' (list of strings), 'formatting_issues' (list of strings).\n"
            "Do NOT output markdown code fences. Just write the raw JSON directly."
        )
        try:
            prompt = f"{system_prompt}\n\nResume Text:\n{text}"
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            raw_text = response.text.strip()
            
            # Clean markdown if model still included it
            if raw_text.startswith("```json"):
                 raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                 raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                 raw_text = raw_text[:-3]
                 
            return json.loads(raw_text.strip())
        except Exception as e:
             # Fallback to gemini-2.0-flash if 2.5 fails
             try:
                 response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                 )
                 raw_text = response.text.strip()
                 if raw_text.startswith("```json"): raw_text = raw_text[7:]
                 elif raw_text.startswith("```"): raw_text = raw_text[3:]
                 if raw_text.endswith("```"): raw_text = raw_text[:-3]
                 return json.loads(raw_text.strip())
             except Exception as fallback_e:
                 return {"error": f"Internal Error assessing resume: {str(e)}"}

class ImprovementAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.is_configured = True
            self.model = "gemini-2.5-flash"
        else:
            self.client = None
            self.is_configured = False

    def suggest_improvements(self, original_text: str, analysis: Dict[str, Any], feedback: str = "") -> str:
        """
        Generates an optimized version of the resume based on analysis and optional user feedback.
        """
        if not self.is_configured:
            return "Error: Gemini API key not configured."
        
        system_prompt = (
            "You are an expert professional Resume Writer. "
            "Your task is to rewrite and optimize the user's resume text. "
            "1. Address the weaknesses and formatting issues identified in the analysis.\n"
            "2. Incorporate strong action verbs, quantify achievements, and ensure standard formatting.\n"
            "3. If user feedback is provided, prioritize it heavily in the revision.\n"
            "Return the FULL revised resume text in Markdown format, with proper headings, bullets, and clear structure. "
            "Do not output anything besides the rewritten resume."
        )

        user_content = f"### Original Resume Text\n{original_text}\n\n"
        if analysis:
            user_content += f"### Analysis Context\n{json.dumps(analysis, indent=2)}\n\n"
        if feedback:
            user_content += f"### User Feedback Context\n{feedback}\n\n"
            
        try:
            prompt = f"{system_prompt}\n\n{user_content}"
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            try:
                 response = self.client.models.generate_content(
                     model="gemini-2.0-flash",
                     contents=prompt
                 )
                 return response.text
            except:
                 return f"Error generating improvements: {str(e)}"
            
    def chat_rewrite(self, current_resume: str, chat_history: List[Dict[str, str]], new_request: str) -> str:
        """
        Iterative rewriting via chat. Adjusts the resume based on conversation.
        """
        if not self.is_configured:
           return "Error: Gemini API key not configured."
        
        system_prompt = (
            "You are a helpful Resume Writer assistant. Your task is to update the provided "
            "resume draft based strictly on the user's latest request. "
            "Reply with the COMPLETE updated resume in Markdown format. "
            "Do NOT include conversational filler like 'Here is the updated resume'. Output only the full resume content."
        )

        history_context = ""
        for msg in chat_history:
             if msg['role'] != 'system':
                history_context += f"{msg['role'].capitalize()}: {msg['content']}\n"
             
        req_content = f"{system_prompt}\n\n### Previous Conversation:\n{history_context}\n\n### Current Resume\n{current_resume}\n\n### User Request\n{new_request}\n\nPlease output the fully rewritten resume."

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=req_content
            )
            return response.text
        except Exception as e:
            try:
                response = self.client.models.generate_content(
                   model="gemini-2.0-flash",
                   contents=req_content
                )
                return response.text
            except:
                return f"Error during chat revision: {str(e)}"
