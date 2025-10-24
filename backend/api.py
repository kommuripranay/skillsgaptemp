# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# -----------------------------
# Load env
# -----------------------------
load_dotenv(".env")
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("Set GOOGLE_API_KEY in .env")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="SkillSync Adaptive Survey API")

# -----------------------------
# Chat model
# -----------------------------
chat_model = ChatGoogleGenerativeAI(
    api_key=google_api_key,
    model="gemini-2.0-flash"
)

# -----------------------------
# Models
# -----------------------------
class StartSurveyRequest(BaseModel):
    user_id: int
    skill_name: str
    skill_level: str  # Beginner / Intermediate / Expert

class AnswerRequest(BaseModel):
    answer: str  # selected option
    time_taken: float  # seconds

# -----------------------------
# Session storage
# -----------------------------
sessions = {}
MAX_QUESTIONS = 15
PLACEMENT_QUESTIONS = 3  # Phase 1 questions

# -----------------------------
# Question prompt template
# -----------------------------
question_prompt_template = ChatPromptTemplate.from_template(
    """
You are an AI that generates ONE skill assessment question for the skill "{skill_name}" at the "{skill_level}" point level.
Provide the question strictly in JSON format:

{{
"question_title": "Question text here",
"opt1": "Option 1",
"opt2": "Option 2",
"opt3": "Option 3",
"opt4": "Option 4"
}}
Do not include anything else.
"""
)

# -----------------------------
# Start survey
# -----------------------------
@app.post("/survey/start")
def start_survey(req: StartSurveyRequest):
    # Map skill_level to numeric bucket
    level_map = {"Beginner": 100, "Intermediate": 500, "Expert": 900}
    base = level_map.get(req.skill_level, 500)
    lower = max(base - 100, 0)
    upper = min(base + 100, 1000)

    sessions[req.user_id] = {
        "user_id": req.user_id,
        "skill_name": req.skill_name,
        "phase": "placement",
        "bucket_range": [lower, upper],
        "min_range": 0,
        "max_range": 1000,
        "current_difficulty": base,
        "current_question_num": 0,
        "answered": [],
        "start_time": time.time(),
        "question_times": [],
        "last_question_time": time.time()
    }

    return {"message": "Survey started", "user_id": req.user_id, "bucket_range": [lower, upper], "phase": "placement"}

# -----------------------------
# Get next question
# -----------------------------
@app.get("/survey/{user_id}/next")
def next_question(user_id: int):
    session = sessions.get(user_id)
    if not session:
        return {"error": "Session not found"}

    if session["phase"] == "completed" or session["current_question_num"] >= MAX_QUESTIONS:
        # Compute final score
        base_score = session.get("bisect_score", session["current_difficulty"])
        avg_time = sum(session["question_times"]) / len(session["question_times"]) if session["question_times"] else 0
        fluency_bonus = max(0, int((30 - avg_time) * 2))  # faster than 30s per question
        final_score = base_score + fluency_bonus
        session["phase"] = "completed"
        return {"message": "Survey completed", "final_score": final_score}

    # Determine difficulty
    if session["phase"] == "placement":
        lower, upper = session["bucket_range"]
        session["current_difficulty"] = (lower + upper) // 2
    elif session["phase"] == "bisection":
        session["current_difficulty"] = (session["min_range"] + session["max_range"]) // 2

    # Generate question
    prompt_text = question_prompt_template.format(
        skill_name=session["skill_name"],
        skill_level=session["current_difficulty"]
    )
    response = chat_model.invoke(prompt_text)
    try:
        question_json = json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": response}

    session["current_question_num"] += 1
    question_json["id"] = session["current_question_num"]
    question_json["start_time"] = time.time()
    session["last_question_time"] = time.time()
    return question_json

# -----------------------------
# Submit answer
# -----------------------------
@app.post("/survey/{user_id}/answer")
def submit_answer(user_id: int, req: AnswerRequest):
    session = sessions.get(user_id)
    if not session:
        return {"error": "Session not found"}

    now = time.time()
    question_time = req.time_taken or (now - session.get("last_question_time", now))
    session["question_times"].append(question_time)
    session["last_question_time"] = now

    # Record answer
    session["answered"].append({
        "qid": session["current_question_num"],
        "answer": req.answer,
        "difficulty": session["current_difficulty"],
        "time_taken": question_time
    })

    # Phase logic
    if session["phase"] == "placement":
        if session["current_question_num"] >= PLACEMENT_QUESTIONS:
            # Simple check: count correct answers (assume opt2 correct for demo)
            correct_count = sum(1 for a in session["answered"] if a["answer"].lower() == "opt2")
            low, high = session["bucket_range"]
            if correct_count >= 2:
                session["min_range"] = high
            else:
                session["max_range"] = low
            session["phase"] = "bisection"
    elif session["phase"] == "bisection":
        last_answer = session["answered"][-1]
        correct_option = "opt2"  # placeholder
        if last_answer["answer"].lower() == correct_option:
            session["min_range"] = session["current_difficulty"]
        else:
            session["max_range"] = session["current_difficulty"]

    # Check for completion
    if session["current_question_num"] >= MAX_QUESTIONS:
        session["phase"] = "completed"

    return {
        "message": "Answer recorded",
        "next_phase": session["phase"],
        "current_range": [session["min_range"], session["max_range"]]
    }

# -----------------------------
# Check session status
# -----------------------------
@app.get("/survey/{user_id}/status")
def check_session(user_id: int):
    session = sessions.get(user_id)
    if not session:
        return {"error": "Session not found"}
    return session
