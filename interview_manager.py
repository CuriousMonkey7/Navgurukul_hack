import ollama
import json

MODEL = "qwen2.5:3b"

class InterviewManager:

    def __init__(self):

        self.history = []
        self.first_question = True

        self.system_prompt = """
You are an expert technical interviewer conducting a project presentation interview.

CRITICAL: You MUST remember and reference the entire conversation history. Each question should build upon what the student has already explained.

Your tasks:
• Pay close attention to everything the student has said throughout the interview
• Reference their previous explanations when asking new questions (e.g., "You mentioned X earlier...")
• Connect different parts of their presentation together
• Ask follow-up questions that dig deeper into topics they've introduced
• Start with broad understanding questions, then progressively drill into technical details
• Test if they truly understand what they've explained by asking "why" and "how" questions
• Be conversational and show you're actively listening
• Focus on: technical implementation, design decisions, trade-offs, and problem-solving approach

IMPORTANT:
- Each question MUST show awareness of previous answers
- Reference specific things they said before
- Build a coherent interview narrative, not isolated questions
- Keep questions under 25 words but make them specific and contextual

Do NOT:
- Ask generic questions that ignore previous context
- Explain answers or provide solutions
- Ask about something they already explained unless digging deeper
"""

        self.history.append({
            "role": "system",
            "content": self.system_prompt
        })


    def ask_question(self, transcript, ocr_text):

        if self.first_question:
            prompt = f"""
This is the first interaction. The student just started presenting.

Student said:
{transcript}

Screen shows:
{ocr_text}

Greet them briefly and ask ONE question about their project to understand what they're building.
"""
            self.first_question = False
        else:
            # Build context summary from recent history
            context_summary = self._get_recent_context()
            
            print(f"\n📚 Context Summary:\n{context_summary}\n")
            
            prompt = f"""
PREVIOUS CONVERSATION CONTEXT:
{context_summary}

STUDENT'S LATEST RESPONSE:
{transcript}

CURRENT SCREEN CONTENT:
{ocr_text}

Based on:
1. What you've learned from the ENTIRE conversation so far
2. Their LATEST response to your previous question
3. What's currently visible on their screen

Ask ONE follow-up question that:
- Builds upon previous discussion (reference what they said before if relevant)
- Explores deeper into topics they mentioned
- Connects different parts of their explanation
- Tests their understanding of what they've explained

Be specific and show you're paying attention to their previous answers.
"""

        self.history.append({
            "role": "user",
            "content": prompt
        })

        response = ollama.chat(
            model=MODEL,
            messages=self.history
        )

        reply = response["message"]["content"]

        self.history.append({
            "role": "assistant",
            "content": reply
        })

        return reply
    
    
    def _get_recent_context(self):
        """Extract recent conversation for context awareness"""
        # Get last 3 Q&A pairs (6 messages) excluding system prompt
        recent = []
        user_messages = [m for m in self.history if m["role"] == "user"]
        assistant_messages = [m for m in self.history if m["role"] == "assistant"]
        
        # Get last 3 exchanges
        num_exchanges = min(3, len(assistant_messages))
        
        for i in range(num_exchanges):
            idx = -(num_exchanges - i)
            if idx < -len(assistant_messages):
                continue
                
            q = assistant_messages[idx]["content"]
            # Find corresponding answer in user messages
            if -(num_exchanges - i) < -len(user_messages):
                continue
            a_full = user_messages[idx]["content"]
            
            # Extract just the student response part
            if "Student said:" in a_full or "Student's response:" in a_full or "STUDENT'S LATEST RESPONSE:" in a_full:
                lines = a_full.split('\n')
                answer_lines = []
                capturing = False
                for line in lines:
                    if "Student" in line or "STUDENT" in line:
                        capturing = True
                        continue
                    if capturing and (line.startswith("Screen") or line.startswith("CURRENT") or line.startswith("Based on")):
                        break
                    if capturing and line.strip():
                        answer_lines.append(line.strip())
                a = " ".join(answer_lines)
            else:
                a = a_full[:150]
            
            recent.append(f"Q: {q}\nA: {a}")
        
        return "\n\n".join(recent) if recent else "First question - no prior context"


    def generate_scorecard(self):

        prompt = """
Based on the entire interview conversation, evaluate the candidate across these dimensions:

1. Technical Depth (1-10): How well do they understand the technical concepts, architecture, and implementation details?

2. Clarity (1-10): How clearly can they explain their project, decisions, and thought process?

3. Originality (1-10): How innovative or creative is their approach or solution?

4. Understanding of Implementation (1-10): How well do they understand what they built and how it works?

Provide a JSON response with scores and constructive feedback:

{
 "technical_depth": <score 1-10>,
 "clarity": <score 1-10>,
 "originality": <score 1-10>,
 "implementation": <score 1-10>,
 "feedback": "<2-3 sentences of constructive feedback highlighting strengths and areas for improvement>"
}

Be fair but honest in your evaluation. Base scores on evidence from the conversation.
"""

        history = self.history.copy()

        history.append({
            "role": "user",
            "content": prompt
        })

        response = ollama.chat(
            model=MODEL,
            messages=history,
            format="json"
        )

        return json.loads(response["message"]["content"])
