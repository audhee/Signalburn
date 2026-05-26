from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
import re
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Literal

from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ----- Models -----
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str

class StatusCheckCreate(BaseModel):
    client_name: str

ScenarioName = Literal[
    "bleeding", "burn", "choking", "cpr", "fainting", "eye_injury", "fracture"
]

class FirstAidRequest(BaseModel):
    scenario: ScenarioName

class FirstAidResponse(BaseModel):
    scenario: ScenarioName
    title: str
    detail: str


# ----- Scenario context for the LLM -----
SCENARIO_CONTEXT = {
    "bleeding": "External bleeding from a wound on the arm or leg.",
    "burn": "A minor thermal burn on the hand or arm from hot surface or liquid.",
    "choking": "An adult is choking and cannot speak or breathe.",
    "cpr": "An adult collapsed and is not breathing normally.",
    "fainting": "A person feels dizzy and is about to faint or has just fainted.",
    "eye_injury": "A chemical or particle has entered the eye.",
    "fracture": "A suspected broken bone in the arm or leg after a fall.",
}

SYSTEM_PROMPT = (
    "You are a calm, reassuring virtual emergency doctor. "
    "Given an emergency scenario, give the FIRST and most important first-aid step a bystander should take. "
    "Respond in STRICT JSON only, no prose, no markdown, no code fences, with EXACTLY this shape: "
    '{"title": "<short imperative instruction, max 8 words>", "detail": "<one short calm sentence with a concrete next action, max 18 words>"}. '
    "Use plain language. Be calm. Do not include disclaimers. Do not mention calling 911 in the title. "
    "Do not include any keys other than title and detail."
)


def _extract_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    # Find first {...}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)


@api_router.get("/")
async def root():
    return {"message": "Emergency Assistant API"}


@api_router.post("/first-aid", response_model=FirstAidResponse)
async def first_aid(req: FirstAidRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    context = SCENARIO_CONTEXT[req.scenario]
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"first-aid-{uuid.uuid4()}",
        system_message=SYSTEM_PROMPT,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    user_msg = UserMessage(
        text=f"Scenario: {req.scenario}. Context: {context}. Provide the first immediate step."
    )

    try:
        raw = await chat.send_message(user_msg)
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    try:
        data = _extract_json(raw if isinstance(raw, str) else str(raw))
        title = str(data.get("title", "")).strip()
        detail = str(data.get("detail", "")).strip()
        if not title or not detail:
            raise ValueError("missing fields")
    except Exception as e:
        logger.error("Failed to parse LLM JSON: %s | raw=%s", e, raw)
        raise HTTPException(status_code=502, detail="Invalid LLM response format")

    result = FirstAidResponse(scenario=req.scenario, title=title, detail=detail)

    # Persist for history (excluding _id on read paths)
    try:
        await db.first_aid_log.insert_one({
            "id": str(uuid.uuid4()),
            "scenario": req.scenario,
            "title": title,
            "detail": detail,
        })
    except Exception:
        logger.exception("DB log failed (non-fatal)")

    return result


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(obj.dict())
    return obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    rows = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    return [StatusCheck(**r) for r in rows]


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()