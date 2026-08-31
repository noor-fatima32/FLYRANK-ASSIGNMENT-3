import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator


load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://openrouter.ai/api/v1",
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openrouter/free",
)
LLM_STUB = os.getenv("LLM_STUB", "1").lower() in {
    "1",
    "true",
    "yes",
}

PROMPT_VERSION = "v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "v1.txt"


app = FastAPI(
    title="FlyRank LLM API",
    description="Support ticket classification API",
    version="1.0.0",
)


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("text must not be empty")

        return value


class ClassifyResponse(BaseModel):
    category: str
    urgency: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_llm_client() -> OpenAI:
    if not LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY must be set in .env"
        )

    return OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )


def call_llm(text: str) -> str:
    prompt = load_prompt()

    client = get_llm_client()

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("LLM returned an empty response")

    return content


def parse_llm_response(content: str) -> ClassifyResponse:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    data = json.loads(cleaned)

    return ClassifyResponse.model_validate(data)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "LLM API is running",
    }


@app.post("/classify", response_model=ClassifyResponse)
def classify(data: ClassifyRequest):
    if LLM_STUB:
        return ClassifyResponse(
            category="other",
            urgency="normal",
            confidence=0.50,
            reason="Stub mode is enabled.",
        )

    try:
        content = call_llm(data.text)
        result = parse_llm_response(content)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM request failed: {str(e)}",
        )