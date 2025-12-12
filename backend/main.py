from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import json
import glob
from backend.engine import load_config, evaluate_candidate, extract_text_from_pdf, load_company_knowledge, detect_companies_in_text

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Consts
CSV_PATH = "postulaciones_FIN-002_2025-12-09.csv"
CVS_DIR = "CVs_FIN-002_2025-12-10"
DB_PATH = "candidates_db.json"

# Models
class Comment(BaseModel):
    author: str
    text: str
    timestamp: str

class InterviewData(BaseModel):
    score: int
    notes: str

class CandidateUpdate(BaseModel):
    comments: Optional[List[Comment]] = None
    interview: Optional[InterviewData] = None

# Helpers
def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def find_cv_path(tracking_code):
    search_pattern = os.path.join(CVS_DIR, f"*{tracking_code}*.pdf")
    matches = glob.glob(search_pattern)
    return matches[0] if matches else None

# Endpoints
@app.get("/api/candidates")
def get_candidates():
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    db = load_db()
    candidates = []
    
    # We do a lightweight load here. 
    # ideally we cache analysis results, but for now we might re-run or rely on DB
    # Let's run a quick analysis loop OR just return metadata if analysis is heavy.
    # Given the small dataset (13 files), we can probably run analysis on the fly or cache it.
    
    config = load_config()
    company_knowledge = load_company_knowledge()
    
    for _, row in df.iterrows():
        tid = row['Código Tracking']
        name = row['Nombre Completo']
        
        # Check if we have cached analysis in DB to avoid re-parsing PDF every time
        candidate_data = db.get(tid, {})
        analysis = candidate_data.get("analysis")
        
        if not analysis:
            # Run analysis if not present
            pdf_path = find_cv_path(tid)
            if pdf_path:
                text = extract_text_from_pdf(pdf_path)
                companies = detect_companies_in_text(text, company_knowledge)
                analysis = evaluate_candidate(text, config, companies)
                
                # Cache it
                candidate_data["analysis"] = analysis
                candidate_data["name"] = name
                db[tid] = candidate_data
                save_db(db)
        
        # Calculate Average Score
        avg_score = 0
        if analysis and "fits" in analysis:
            scores = [v["score"] for v in analysis["fits"].values()]
            if scores:
                avg_score = int(sum(scores) / len(scores))
        
        candidates.append({
            "id": tid,
            "name": name,
            "email": row.get('Email', ''),
            "phone": row.get('Teléfono', ''),
            "score_avg": avg_score,
            "risk": analysis.get("inference", {}).get("retention_risk", "N/A") if analysis else "N/A",
            "hands_on": analysis.get("inference", {}).get("hands_on_index", 0) if analysis else 0,
            "interview_status": "Entrevistado" if candidate_data.get("interview") else "Pendiente"
        })
        
    # Sort by score desc
    candidates.sort(key=lambda x: x['score_avg'], reverse=True)
    return candidates

@app.get("/api/candidates/{candidate_id}")
def get_candidate_detail(candidate_id: str):
    db = load_db()
    
    # Reload config to ensure we apply latest settings if user changed them
    config = load_config()
    company_knowledge = load_company_knowledge()
    
    # Look up in CSV for static data
    try:
        df = pd.read_csv(CSV_PATH)
        row = df[df['Código Tracking'] == candidate_id].iloc[0]
    except:
        raise HTTPException(status_code=404, detail="Candidate not found in CSV")
        
    candidate_data = db.get(candidate_id, {})
    
    # Always re-analyze to reflect config changes or if missing
    pdf_path = find_cv_path(candidate_id)
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
        
    text = extract_text_from_pdf(pdf_path)
    companies = detect_companies_in_text(text, company_knowledge)
    analysis = evaluate_candidate(text, config, companies)
    
    # Update DB with fresh analysis but keep comments/interview
    candidate_data["analysis"] = analysis
    candidate_data["name"] = row['Nombre Completo']
    db[candidate_id] = candidate_data
    save_db(db)
    
    return {
        "metadata": {
            "name": row['Nombre Completo'],
            "email": row['Email'],
            "phone": row['Teléfono'],
            "applied_at": row['Fecha Postulación'],
            "tracking_id": candidate_id
        },
        "analysis": analysis,
        "comments": candidate_data.get("comments", []),
        "interview": candidate_data.get("interview", None),
        "pdf_url": f"/files/{os.path.basename(pdf_path)}"
    }

@app.post("/api/candidates/{candidate_id}/comment")
def add_comment(candidate_id: str, comment: Comment):
    db = load_db()
    if candidate_id not in db:
        db[candidate_id] = {}
    
    comments = db[candidate_id].get("comments", [])
    comments.append(comment.dict())
    db[candidate_id]["comments"] = comments
    save_db(db)
    return {"status": "ok", "comments": comments}

@app.post("/api/candidates/{candidate_id}/interview")
def update_interview(candidate_id: str, interview: InterviewData):
    db = load_db()
    if candidate_id not in db:
        db[candidate_id] = {}
        
    db[candidate_id]["interview"] = interview.dict()
    save_db(db)
    return {"status": "ok"}

@app.post("/api/config")
def update_config(new_config: Dict[str, Any]):
    try:
        with open("backend/model_config.json", "w") as f:
            json.dump(new_config, f, indent=2)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_config():
    return load_config()

@app.get("/files/{filename}")
def serve_file(filename: str):
    file_path = os.path.join(CVS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")
