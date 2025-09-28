# NLP Query Engine - Demo (Minimal Working Implementation)

This repository is a *minimal, runnable demo* that implements core parts of the assignment:
- dynamic schema discovery (SQLAlchemy reflection)
- document ingestion (txt/csv) + TF-IDF index (scikit-learn)
- a QueryEngine that heuristically maps simple NL queries to SQL or document search
- a lightweight single-page frontend (HTML + JS) to interact with the API

## Screen UI
<img width="1870" height="879" alt="Screenshot 2025-09-28 163354" src="https://github.com/user-attachments/assets/ba502e86-a1aa-4a24-9168-ad4d04eed286" />


## Quick start (run on your machine)
1. `cd` into the project folder.
2. Create and activate a Python virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. (Optional) Preload sample resumes into the document index:
   ```bash
   python -m backend.preload_resumes
   ```
5. Start the server:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
6. Open http://localhost:8000/ in your browser.

## Example queries
- How many employees do we have?
- Average salary by department
- Show me employees
- Find resumes with Python

