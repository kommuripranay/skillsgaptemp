from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import json
import re

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("Set GOOGLE_API_KEY in .env")

# -----------------------------
# Initialize FastAPI app
# -----------------------------
app = FastAPI(title="Adaptive Skill Evaluation API")

# -----------------------------
# Initialize Gemini LLM
# -----------------------------
llm = ChatGoogleGenerativeAI(
    api_key=google_api_key,
    model="gemini-2.0-flash",
    temperature=0.7
)

# -----------------------------
# Models for requests
# -----------------------------
class StartTestRequest(BaseModel):
    user_id: str
    skill: str
    self_rating: int  # between 0–100

class AnswerRequest(BaseModel):
    user_id: str
    question_id: int
    selected_option: str
    time_taken: float  # seconds
    previous_level: int  # 0–100
    correct_answer: str

class EndTestRequest(BaseModel):
    user_id: str
    skill: str

# -----------------------------
# Prompt Template
# -----------------------------
question_prompt = ChatPromptTemplate.from_template("""
You are an expert technical test designer for adaptive skill assessments.

The user is being tested for the skill: **{skill}**
They believe their level is **{level}/100**

Difficulty buckets:
- 0 - 20: very basic and conceptual
- 20 - 40: beginner
- 40 - 60: intermediate
- 60 - 80: advanced
- 80 - 100: expert

Instructions:
- Generate ONE multiple choice question.
- Avoid repeating any question from previous history.
- Use the difficulty bucket nearest to the user's current estimated skill level.
- Each question must be relevant to real-world application of the skill.
- Include 4 options, with only one correct answer.
- Use neutral, professional wording.

Additional Context:
- Previous questions and user responses: {history}

Return only valid JSON (no markdown) in the structure:

{{
"question_id": {qid},
"question_title": "string",
"options": {{
    "opt1": "string",
    "opt2": "string",
    "opt3": "string",
    "opt4": "string"
}},
"correct_answer": "optX",
"difficulty": {level}
}}
""")

# -----------------------------
# Helper function to clean LLM JSON
# -----------------------------
def clean_llm_json(llm_text: str) -> str:
    llm_text = re.sub(r'^```json\s*', '', llm_text.strip(), flags=re.MULTILINE)
    llm_text = re.sub(r'```$', '', llm_text.strip(), flags=re.MULTILINE)
    return llm_text

# -----------------------------
# In-memory store (prototype)
# -----------------------------
active_sessions = {}

# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/start_test")
async def start_test(req: StartTestRequest):
    """
    Start a new adaptive test session for a user & skill.
    Generates the first question.
    """
    user_session = {
        "user_id": req.user_id,
        "skill": req.skill,
        "current_level": req.self_rating,
        "questions_asked": 0,
        "correct_answers": 0,
        "history": []  # stores question, options, correct_answer, user_answer
    }

    active_sessions[req.user_id] = user_session

    # Generate first question
    try:
        history_json = json.dumps(user_session["history"])
        prompt = question_prompt.format_messages(
            skill=req.skill,
            level=req.self_rating,
            qid=1,
            history=history_json
        )
        response = llm.invoke(prompt)
        cleaned_response = clean_llm_json(response.content)
        question = json.loads(cleaned_response)

        # Store question in session history
        user_session["history"].append({
            "question_id": question["question_id"],
            "question_title": question["question_title"],
            "options": question["options"],
            "correct_answer": question["correct_answer"],
            "user_answer": None,
            "difficulty": question["difficulty"]
        })
        user_session["last_question"] = question
        user_session["questions_asked"] += 1
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {str(e)}")


@app.post("/next_question")
async def next_question(req: AnswerRequest):
    """
    Generate next question based on user response and history.
    """
    session = active_sessions.get(req.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active test session found.")

    # Update user's answer in history
    if session["last_question"]["question_id"] != req.question_id:
        raise HTTPException(status_code=400, detail="Question ID mismatch.")
    
    for q in session["history"]:
        if q["question_id"] == req.question_id:
            q["user_answer"] = req.selected_option
            break

    # Adjust skill level based on correctness and time
    level = session["current_level"]
    time_factor = max(0.5, min(1.5, 30 / (req.time_taken + 1)))  # ideal 30s

    if req.selected_option == req.correct_answer:
        new_level = min(100, int(level + (5 * time_factor)))
        session["correct_answers"] += 1
    else:
        new_level = max(0, int(level - (5 / time_factor)))

    session["current_level"] = new_level

    # Generate next question
    try:
        history_json = json.dumps(session["history"])
        prompt = question_prompt.format_messages(
            skill=session["skill"],
            level=new_level,
            qid=session["questions_asked"] + 1,
            history=history_json
        )
        response = llm.invoke(prompt)
        cleaned_response = clean_llm_json(response.content)
        question = json.loads(cleaned_response)

        # Store question in session history
        session["history"].append({
            "question_id": question["question_id"],
            "question_title": question["question_title"],
            "options": question["options"],
            "correct_answer": question["correct_answer"],
            "user_answer": None,
            "difficulty": question["difficulty"]
        })
        session["last_question"] = question
        session["questions_asked"] += 1
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate next question: {str(e)}")


@app.post("/end_test")
async def end_test(req: EndTestRequest):
    """
    Ends the test and returns final score.
    """
    session = active_sessions.pop(req.user_id, None)
    if not session:
        raise HTTPException(status_code=404, detail="No active test found for user.")

    # Compute score
    score = (session["correct_answers"] / max(1, session["questions_asked"])) * 100

    return {
        "user_id": req.user_id,
        "skill": req.skill,
        "final_score": round(score, 2),
        "questions_attempted": session["questions_asked"],
        "history": session["history"]
    }
