# IPF IPA PoC - Setup Guide

## Project Structure
src/
  backend/
    core/        - config.py, database.py
    agents/      - document_agent.py, validator.py, orchestrator.py
    api/         - main.py (FastAPI)
  admin_ui/      - admin_app.py (Streamlit)
  reviewer_ui/   - reviewer_app.py (Streamlit)

## Prerequisites
- Python 3.11+
- Supabase account (free tier)
- OpenAI API key

## Step 1: Supabase Setup
1. Go to supabase.com and create a new project
2. Run the SQL in scripts/supabase_schema.sql in the SQL editor
3. Create a storage bucket called "documents" (public read)
4. Copy your project URL and keys

## Step 2: Environment Variables
Copy .env.example to .env and fill in your values:
  SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
  OPENAI_API_KEY
  BACKEND_URL (use http://localhost:8000 for local)

## Step 3: Install Dependencies
  python -m pip install -r requirements.txt

## Step 4: Run the Backend
  uvicorn src.backend.api.main:app --reload --port 8000

## Step 5: Run Admin UI (new terminal)
  streamlit run src/admin_ui/admin_app.py --server.port 8501

## Step 6: Run Reviewer UI (new terminal)
  streamlit run src/reviewer_ui/reviewer_app.py --server.port 8502

## Default Passwords
  Admin:    ipf-admin-2026
  Reviewer: ipf-reviewer-2026
  Assessor: ipf-assessor-2026

## Test the Flow
1. Open http://localhost:8501 (Admin) - upload test PDFs from test-data/
2. AI processes automatically
3. Open http://localhost:8502 (Reviewer) - review and approve
