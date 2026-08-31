import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(
    title="FlyRank LLM API",
    description="Support ticket classification API",
    version="1.0.0",
)


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class ClassifyResponse(BaseModel):
    category: str
    urgency: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "LLM API is running",
    }


@app.post("/classify", response_model=ClassifyResponse)
def classify(data: ClassifyRequest):
    text = data.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="text must not be empty",
        )

    # Temporary stub response.
    # The real LLM call will be added in Stage 2.
    return ClassifyResponse(
        category="other",
        urgency="normal",
        confidence=0.50,
        reason="Temporary stub response.",
    )