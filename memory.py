import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SessionMemory(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_resume: str = ""
    current_resume: str = ""
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    improvement_history: List[Dict[str, Any]] = Field(default_factory=list)
    chat_history: List[Dict[str, str]] = Field(default_factory=list) # [{'role': 'user'|'assistant', 'content': ''}]

    def set_original_resume(self, content: str):
        self.original_resume = content
        self.current_resume = content

    def set_analysis(self, analysis_data: Dict[str, Any]):
        self.analysis_results = analysis_data

    def update_resume(self, new_resume: str, feedback: str = "", metadata: Optional[Dict] = None):
        if self.current_resume:
            self.improvement_history.append({
                "previous": self.current_resume,
                "feedback_applied": feedback,
                "metadata": metadata or {}
            })
        self.current_resume = new_resume

    def add_message(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})

    def get_conversation_context(self, limit: int = 5) -> str:
        """Returns the last 'limit' messages formatted for agent context."""
        context = ""
        recent = self.chat_history[-limit:]
        for msg in recent:
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context

    def get_gradio_chat_history(self) -> List[List[Optional[str]]]:
        """Formats chat history for Gradio Chatbot component: List of [user_msg, bot_msg]"""
        gradio_history = []
        user_msg = None
        for msg in self.chat_history:
            if msg["role"] == "user":
                if user_msg is not None: # Missing assistant response for previous message
                   gradio_history.append([user_msg, None]) 
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                gradio_history.append([user_msg, msg["content"]])
                user_msg = None
        
        if user_msg is not None:
             gradio_history.append([user_msg, None])
             
        return gradio_history

    def clear(self):
        self.original_resume = ""
        self.current_resume = ""
        self.analysis_results = {}
        self.improvement_history.clear()
        self.chat_history.clear()
        self.session_id = str(uuid.uuid4())
