# AI-Assisted Exam Evaluation System

A production-ready platform for universities to generate exams, evaluate subjective answers, and provide AI-driven feedback.

## Features

- **Role-Based Access**: Students, Teachers
- **AI Exam Generation**: RAG-based question generation from course PDFs.
- **Auto-Grading**: GPT-4o evaluation of student answers with detailed feedback.
- **Handwriting Support**: OCR for physical exam papers.
- **Course Management**: Teachers can manage subjects and materials.

## Tech Stack

- **Backend**: FastAPI, PostgreSQL (pgvector), LangChain, OpenAI.
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn UI (concepts).
- **Database**: Supabase (PostgreSQL).

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL (or Supabase URL)
- OpenAI API Key

### Backend Setup
1. Navigate to backend: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env`:
   ```bash
   POSTGRES_SERVER=...
   POSTGRES_USER=...
   POSTGRES_PASSWORD=...
   POSTGRES_DB=...
   OPENAI_API_KEY=...
   ```
4. Run Migrations: `alembic upgrade head`
5. Start Server: `uvicorn app.main:app --reload`

### Frontend Setup
1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Start Dev Server: `npm run dev`
4. Access App: `http://localhost:3000`

## API Documentation
Once backend is running, visit `http://localhost:8000/docs` for Swagger UI.
