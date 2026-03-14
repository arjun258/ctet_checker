"""
api.py  —  FastAPI backend for CTET OMR Answer Checker
Place this in your OMRChecker root folder alongside ctet_check.py

Install dependencies:
    pip install fastapi uvicorn python-multipart

Run with:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import csv as csv_module
import glob
import os
import shutil
import sys
import uuid
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Import checking logic from ctet_check.py ─────────────────
# We reuse the answer keys and checking functions directly
# so there's no subprocess — it's all in-process and fast.
sys.path.insert(0, os.path.dirname(__file__))
from ctet_check import (
    ANSWER_KEYS,
    LETTER_TO_NUM,
    NUM_TO_LETTER,
    find_template,
    parse_omr_csv,
    check_section,
)

import subprocess

app = FastAPI(title="CTET OMR Checker API", version="1.0")

# Allow the HTML frontend (served from any origin during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Serve the frontend HTML as a static file at /
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")


# ════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════
from fastapi.responses import FileResponse
@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════
# MAIN ENDPOINT: POST /check
# ════════════════════════════════════════════════════════════════

@app.post("/check")
async def check_omr(
    image:       UploadFile = File(...,  description="OMR sheet image (JPG/PNG)"),
    subject:     str        = Form(...,  description="math_science or social_science"),
    subject_set: str        = Form(...,  description="G, H, I, or J"),
    lang1:       str        = Form(...,  description="English or Hindi"),
    lang1_set:   str        = Form(...,  description="G, H, I, or J"),
    lang2:       str        = Form(...,  description="English or Hindi"),
    lang2_set:   str        = Form(...,  description="G, H, I, or J"),
):
    """
    Upload an OMR image + paper details → get back the full score breakdown.
    """

    # ── 1. Validate inputs ────────────────────────────────────
    valid_subjects  = {"math_science", "social_science"}
    valid_sets      = {"G", "H", "I", "J"}
    valid_languages = {"English", "Hindi"}

    subject_set = subject_set.upper()
    lang1_set   = lang1_set.upper()
    lang2_set   = lang2_set.upper()

    errors = []
    if subject not in valid_subjects:
        errors.append(f"subject must be one of {valid_subjects}")
    if subject_set not in valid_sets:
        errors.append(f"subject_set must be one of {valid_sets}")
    if lang1 not in valid_languages:
        errors.append(f"lang1 must be one of {valid_languages}")
    if lang1_set not in valid_sets:
        errors.append(f"lang1_set must be one of {valid_sets}")
    if lang2 not in valid_languages:
        errors.append(f"lang2 must be one of {valid_languages}")
    if lang2_set not in valid_sets:
        errors.append(f"lang2_set must be one of {valid_sets}")
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    omrchecker_dir = os.path.abspath(os.path.dirname(__file__))

    # ── 2. Save uploaded image to temp session folder ─────────
    session_id  = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:10]}"
    input_dir   = os.path.join(omrchecker_dir, "inputs",  f"session_{session_id}")
    images_dir  = os.path.join(input_dir, "IMAGES")
    output_dir  = os.path.join(omrchecker_dir, "outputs", f"session_{session_id}")

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Write uploaded image
    ext        = os.path.splitext(image.filename)[1] or ".jpg"
    image_path = os.path.join(images_dir, f"omr{ext}")
    contents   = await image.read()
    with open(image_path, "wb") as f:
        f.write(contents)

    # Copy template.json
    template_src = find_template(omrchecker_dir)
    if not template_src:
        raise HTTPException(status_code=500, detail="template.json not found on server.")
    shutil.copy2(template_src, os.path.join(input_dir, "template.json"))

    # ── 3. Run OMRChecker as subprocess ──────────────────────
    env = os.environ.copy()
    env["OMR_SESSION_ID"] = session_id

    cmd = [
        sys.executable,
        os.path.join(omrchecker_dir, "main.py"),
        "--inputDir",  input_dir,
        "--outputDir", output_dir,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=omrchecker_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="OMRChecker timed out after 120s.")

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"OMRChecker failed:\n{result.stderr[-1000:]}"
        )

    # ── 4. Find and parse the CSV ─────────────────────────────
    matches = glob.glob(os.path.join(output_dir, "**", f"Results_{session_id}.csv"), recursive=True)
    if not matches:
        matches = glob.glob(os.path.join(output_dir, "**", "Results_*.csv"), recursive=True)
    if not matches:
        raise HTTPException(status_code=500, detail="No Results CSV found after OMR scan.")

    candidate_answers = parse_omr_csv(matches[0])
    if not candidate_answers:
        raise HTTPException(status_code=500, detail="CSV was empty — OMR scan may have failed.")

    # ── 5. Check answers ──────────────────────────────────────
    subj_key   = ANSWER_KEYS[subject][f"Set_{subject_set}"]
    lang1_full = ANSWER_KEYS["languages"][lang1][f"Set_{lang1_set}"]
    lang2_full = ANSWER_KEYS["languages"][lang2][f"Set_{lang2_set}"]

    lang1_key = {q: v for q, v in lang1_full.items() if 91  <= q <= 120}
    lang2_key = {q: v for q, v in lang2_full.items() if 121 <= q <= 150}

    s1, t1, d1 = check_section(candidate_answers, subj_key,  1,   90)
    s2, t2, d2 = check_section(candidate_answers, lang1_key, 91,  120)
    s3, t3, d3 = check_section(candidate_answers, lang2_key, 121, 150)

    total = s1 + s2 + s3

    # ── 6. Build response ─────────────────────────────────────
    subject_label = "Maths & Science" if subject == "math_science" else "Social Science"

    def fmt_details(details):
        return [
            {
                "q":       d["q"],
                "you":     d["you"],
                "correct": d["correct"],
                "status":  d["status"],
            }
            for d in details
        ]

    return JSONResponse({
        "session_id": session_id,
        "total":      total,
        "max":        150,
        "passed":     total >= 90,
        "percentage": round(total / 150 * 100, 1),
        "sections": {
            "subject": {
                "label":   f"CDP + {subject_label}",
                "set":     subject_set,
                "score":   s1,
                "max":     t1,
                "pct":     round(s1 / t1 * 100, 1),
                "details": fmt_details(d1),
            },
            "lang1": {
                "label":   lang1,
                "set":     lang1_set,
                "score":   s2,
                "max":     t2,
                "pct":     round(s2 / t2 * 100, 1),
                "details": fmt_details(d2),
            },
            "lang2": {
                "label":   lang2,
                "set":     lang2_set,
                "score":   s3,
                "max":     t3,
                "pct":     round(s3 / t3 * 100, 1),
                "details": fmt_details(d3),
            },
        },
    })