from fastapi import FastAPI
from pydantic import BaseModel, AnyHttpUrl
from typing import Optional

app = FastAPI()

class AnalyzeBody(BaseModel):
    front_url: AnyHttpUrl
    back_url: Optional[AnyHttpUrl] = None
    set_hint: Optional[str] = None

@app.post("/analyze")
def analyze(body: AnalyzeBody):
    return {
        "centering": {"front": None, "back": None},
        "surface": {"front": None, "back": None},
        "grade_estimate": {"pred": "PSA 9", "confidence": 0.65, "reasons": ["placeholder"]},
        "thresholds": {"front_10": "55/45", "back_10": "75/25"}
    }
