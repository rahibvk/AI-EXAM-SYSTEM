# AI Hybrid Assessment System

A comprehensive, production-ready platform for modernizing the educational assessment lifecycle. This system unifies online and offline exam management, leveraging advanced AI (RAG & LLMs) to generate high-quality questions, automate grading, and provide actionable feedback.

## Key Features

### 🎓 Student Management
- **Unified Roster**: Teachers can view and manage all students in a centralized dashboard.
- **Easy Enrollment**: Enrolling students into courses via email or name search.
- **Access Control**: Role-based permissions ensuring students only access their assigned assessments.

### 📝 Exam Generation (AI-Powered)
- **RAG Integration**: Upload course materials (PDFs/Text) to generate context-aware questions.
- **Hybrid Modes**: Support for both **Online** (Real-time interface) and **Offline** (PDF generation for paper exams) assessments.
- **Customizable**: Configure difficulty levels, question counts (Subjective/Objective), and grading criteria.

### 🤖 Intelligent Grading
- **AI Evaluation**: Automated grading of subjective answers using GPT-4o, providing detailed feedback and explanations.
- **Bulk Offline Processing**: seamless workflow for scanning and uploading batches of handwritten answer sheets.
- **OCR Capability**: Integrated Vision AI to transcribe and grade physical exam papers.
- **Manual Override**: Teachers retain full control to review, edit, and finalize AI-suggested grades.

### 📊 Dashboards & Analytics
- **Teacher Portal**: comprehensive tools for course management, exam creation, and student tracking.
- **Student Portal**: clean interface for taking upcoming exams and viewing detailed performance results.

## Tech Stack

- **Backend**: FastAPI (Python), LangChain, OpenAI (GPT-4o), PostgreSQL (Supabase), pgvector.
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn UI.
- **Database**: PostgreSQL (via Supabase) with SQLAlchemy ORM.
- **Security**: JWT Authentication (Stateless, HS256), Bcrypt Password Hashing, HTTPS.

## 🚀 Getting Started (Run from Source)

Follow these instructions to build and run the application from the provided source code files.

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- **PostgreSQL Database** (We use Supabase, but a local Postgres instance works too)
- **OpenAI API Key** (Required for AI generation and grading)

### 2. Backend Setup
The backend handles the API, Database connections, and AI processing.

1.  **Open a terminal** and navigate to the `backend` folder:
    ```bash
    cd backend
    ```

2.  **Create a Virtual Environment** (Recommended to isolate dependencies):
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a file named `.env` inside the `backend` folder and add your credentials:
    ```env
    POSTGRES_SERVER=your_supabase_host
    POSTGRES_USER=your_db_user
    POSTGRES_PASSWORD=your_db_password
    POSTGRES_DB=your_db_name
    POSTGRES_PORT=5432
    OPENAI_API_KEY=sk-...
    SECRET_KEY=your_secure_secret_key
    ```
    *(Note: Ensure your database allows connections from your IP)*

5.  **Initialize the Database**:
    Run the migration script to create tables:
    ```bash
    alembic upgrade head
    ```

6.  **Start the Backend Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
    *The API will be live at `http://localhost:8000`*

### 3. Frontend Setup
The frontend provides the user interface for Teachers and Students.

1.  **Open a new terminal window** and navigate to the `frontend` folder:
    ```bash
    cd frontend
    ```

2.  **Install Node Dependencies**:
    ```bash
    npm install
    ```

3.  **Start the Development Server**:
    ```bash
    npm run dev
    ```
    *The application will be accessible at `http://localhost:3000`*

## 📚 API Documentation
Once the backend is running, you can access the full interactive Swagger documentation to test endpoints directly:
- **URL**: `http://localhost:8000/docs`
