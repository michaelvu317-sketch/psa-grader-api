# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, AnyHttpUrl
from typing import Optional, List

app = FastAPI()

# ---- health ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- request model ----
class AnalyzeBody(BaseModel):
    front_url: AnyHttpUrl
    back_url: Optional[AnyHttpUrl] = None
    set_hint: Optional[str] = None

# PSA tolerances (adjust if you already define these elsewhere)
FRONT_TOL = (55, 45)
BACK_TOL = (75, 25)

# NOTE: This file assumes you already have these functions defined/imported somewhere:
# - url_to_bgr(url: str) -> np.ndarray
# - rectify_card(img_bgr) -> np.ndarray
# - measure_centering(rect_bgr) -> dict(left=..., right=..., top=..., bottom=...)
# - meets_tolerance(left,right,top,bottom, tol=(..., ...)) -> bool
# - surface_heuristics(rect_bgr) -> dict(...)
#
# If you don't, either import them here or replace the calls with your own logic.

@app.post("/analyze")
def analyze(body: AnalyzeBody):
    # ---- FRONT (required) ----
    try:
        front = url_to_bgr(str(body.front_url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to fetch/parse front_url: {e}")

    front_r = rectify_card(front)
    c_front = measure_centering(front_r)
    c_front['meets_psa10'] = meets_tolerance(
        c_front['left'], c_front['right'], c_front['top'], c_front['bottom'], FRONT_TOL
    )

    surface_front = surface_heuristics(front_r)

    # ---- BACK (optional) ----
    c_back = None
    surface_back = None
    if body.back_url:
        try:
            back = url_to_bgr(str(body.back_url))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to fetch/parse back_url: {e}")

        back_r = rectify_card(back)
        c_back = measure_centering(back_r)
        c_back['meets_psa10'] = meets_tolerance(
            c_back['left'], c_back['right'], c_back['top'], c_back['bottom'], BACK_TOL
        )
        surface_back = surface_heuristics(back_r)

    # ---- Simple grade heuristic: start at 10, apply deductions ----
    grade = 10
    reasons: List[str] = []

    # Centering checks
    if not c_front['meets_psa10']:
        reasons.append('Front centering outside PSA10 tolerance')
        grade = min(grade, 9)

    if c_back and not c_back['meets_psa10']:
        reasons.append('Back centering outside PSA10 tolerance')
        grade = min(grade, 9)

    # Edge whitening heuristic
    ew = surface_front['edge_whitening_pct']
    if ew > 0.5:
        grade = min(grade, 9)
        reasons.append(f'Edge whitening ~{ew:.1f}% perimeter pixels')

    if surface_back:
        ew2 = surface_back['edge_whitening_pct']
        if ew2 > 0.5:
            grade = min(grade, 9)
            reasons.append(f'Back edge whitening ~{ew2:.1f}%')

    # Quality warnings reduce confidence
    warnings: List[str] = []
    warnings += surface_front.get('warnings', [])
    if surface_back:
        warnings += surface_back.get('warnings', [])

    # Confidence: naive baseline 0.65, lower with warnings
    conf = 0.65
    conf -= 0.05 * len(warnings)
    conf = max(0.2, min(0.9, conf))

    # Default reason if none were added
    if not reasons:
        reasons = ['Strong centering and minimal visible surface issues']

    return {
        'centering': {
            'front': c_front,
            'back': c_back or None
        },
        'surface': {
            'front': surface_front,
            'back': surface_back or None
        },
        'grade_estimate': {
            'pred': f'PSA {grade}',
            'confidence': round(conf, 2),
            'reasons': reasons
        },
        'thresholds': {
            'front_10': '55/45',
            'back_10': '75/25'
        }
    }
