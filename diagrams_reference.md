# Project Diagrams Reference

This document contains the source code (Mermaid) and detailed explanatory narratives for every architectural diagram in the system. These explanations are written to ensure that a reader who has never seen the application can fully understand its structure and workflow.

---

## 1. System Context Diagram (Level 1)

### Narrative Explanation
**Imagine looking at the system from 10,000 feet up.** This diagram describes the **AI Assessment System** as a black box and shows strictly who interacts with it.
*   **The Users**: On the left, we have the **Teacher**, who acts as the content creator (uploading PDFs, generating exams), and the **Student**, who acts as the consumer (taking exams).
*   **The Bridge**: The "AI Assessment System" sits in the middle. Its job is to bridge the gap between these two users. It takes the teacher's raw files and converts them into interactive exams for the student.
*   **The Brain**: On the right, you see **OpenAI**. This is crucial because our system doesn't "know" biology or physics itself. It relies on an external "brain" (OpenAI's GPT-4o) to generate questions and grade answers. This line shows that our system is dependent on an internet connection and a third-party service to function smart.

### Mermaid Code
```mermaid
graph LR
    %% Actors
    Teacher["👩‍🏫 Teacher<br/>[User]"]
    Student["👨‍🎓 Student<br/>[User]"]

    %% System
    System["AI Assessment System<br/>[Software System]"]

    %% Externa Systems
    OpenAI["OpenAI API<br/>[External SaaS]"]

    %% Relationships
    Teacher -- "Uploads Content, Creates Exams" --> System
    Student -- "Takes Exams, Views Results" --> System
    System -- "Sends Prompts / Vision Requests" --> OpenAI

    classDef focus fill:#1168bd,stroke:#0b4884,color:#ffffff
    class System focus
```

---

## 2. Container Diagram (Level 2)

### Narrative Explanation
**Now let's open the black box.** This diagram explains the technology stack—the actual software programs running on the server.
*   **The Face (Web Application)**: The top box is what the users see. It is built with **Next.js**. Think of this as the "waiter" in a restaurant. It takes orders (clicks, inputs) from the user and shows them the menu (UI), but it doesn't cook the food.
*   **The Brain (API Server)**: The middle box is the kitchen. Built with **FastAPI (Python)**, this is where the actual work happens. When a student submits an exam, the "waiter" brings it here. This server decides if the answer is right or wrong by talking to OpenAI.
*   **The Memory (Database)**: The bottom cylinder is the refrigerator. It stores all the long-term data—user accounts, exam scores, and even the course textbooks (converted into mathematical search vectors). We use **PostgreSQL**, a robust industry-standard database.
*   **Significance**: The separation between the "Web App" and "API Server" means we can update the website design without breaking the grading logic, and vice versa.

### Mermaid Code
```mermaid
graph TD
    %% Actors
    Teacher((Teacher))
    Student((Student))

    %% Boundaries
    subgraph "Docker Host / Cloud Instance"
        %% Containers
        WebApp["Web Application<br/>[Next.js 16/Node]"]
        
        API["API Server<br/>[FastAPI/Python]"]
        
        DB[("Database<br/>[PostgreSQL + pgvector]")]
    end

    %% External
    GPT("OpenAI GPT-4o<br/>[LLM API]")

    %% Connections
    Teacher -->|HTTPS/Browser| WebApp
    Student -->|HTTPS/Browser| WebApp

    WebApp -->|JSON/REST| API

    API -->|SQL/asyncpg| DB
    API -->|HTTPS/JSON| GPT

    %% Styling
    style DB fill:#eee,stroke:#999
    style GPT fill:#ddd,stroke:#999,stroke-dasharray: 5 5
```

---

## 3. Component Diagram (Backend API)

### Narrative Explanation
**Let's look inside the "Brain" (API Server).** This diagram shows the internal assembly line of our software.
*   **The Gatekeeper (Router & Auth)**: Every request first hits the **Router**. Beside it is the **Auth Dependency**. Think of this as a security guard checking ID badges. If a student tries to access a teacher's grading panel, this component stops them immediately.
*   **The Assembly Lines (Services)**: Once inside, tasks are sent to specialized departments:
    *   **Exam Generator**: This department reads textbooks (`Fetch Material`) and asks the AI (`Prompt`) to write questions.
    *   **Evaluation Service**: This department acts as the grader. It compares student answers against the rubric.
    *   **Bulk Grading**: This is a special department for paper exams. It first sends the image to an **OCR Service** (which reads handwriting) before passing the text to the standard grader.
    *   **Analytics**: This is the reporting desk. It doesn't use AI; it just counts numbers in the database to show charts.
*   **Significance**: This structure shows that our code is "Modular". The *Bulk Grading* service reuses the *Evaluation Service*, proving that we wrote the grading logic once and reused it everywhere.

### Mermaid Code
```mermaid
graph TD
    %% Inbound
    Req[HTTP Request] --> Router[API Router]

    %% Internal Components
    subgraph "API Service Layer"
        Router --> Auth[Auth Dependency]
        
        %% Exam Logic
        Router --> ExamGen[Exam Generator Service]
        ExamGen -->|Fetch Material| CRUD[CRUD Layer]
        ExamGen -->|Prompt| LLM[LangChain Client]

        %% Analytics Logic
        Router --> Analytics["Analytics Endpoint (users.py)"]
        Analytics -->|Count Queries| CRUD

        %% Grading Logic
        Router --> Eval[Evaluation Service]
        Eval -->|Prompt| LLM

        %% Bulk Logic
        Router --> Bulk[Bulk Grading Service]
        Bulk --> OCR[OCR Service]
        OCR --> LLM
        Bulk --> Eval
    end

    %% Outbound
    CRUD --> DB[(Database)]
    LLM --> OpenAI(OpenAI Cloud)

    %% Styling
    style Router fill:#f9f,stroke:#333
    style LLM fill:#bbf,stroke:#333
    style Analytics fill:#dfd,stroke:#333
```

---

## 4. Deployment Diagram

### Narrative Explanation
**Where does this actually run?** This diagram maps the software to the physical world.
*   **User Device**: This represents the student's or teacher's laptop. Notice the only thing running here is a **Web Browser**. They do not need to install any special software.
*   **Production Server**: This is the computer we control (likely a cloud server).
    *   **Private Network**: Inside this server, we created a secure "bubble" (Docker Network). The Database (Port 5432) and API (Port 8000) live inside this bubble.
    *   **Exposure**: Only the Web Container (Next.js) and API are listening for outside commands. The Database is hidden safely behind them.
*   **Significance**: This setup is "Self-Contained". We can copy this entire "Production Server" block, move it to another cloud provider (like AWS or Azure), and it would work exactly the same way.

### Mermaid Code
```mermaid
graph TD
    %% Nodes
    subgraph "User Device"
        Browser["Web Browser"]
    end

    subgraph "Production Server (Docker Compose)"
        %% ReverseProxy["Nginx / Ingress"] - Planned for Prod, currently direct access
        
        subgraph "App Network (Private)"
            NextContainer["Next.js Container<br/>Port: 3000"]
            FastAPIContainer["FastAPI Container<br/>Port: 8000"]
            PostgresContainer["Postgres Container<br/>Port: 5432"]
        end
    end

    %% External
    Cloud["Internet / Cloud"]

    %% Edges
    Browser -- "HTTP:3000" --> Cloud
    Cloud -- "HTTP" --> NextContainer
    NextContainer -- "API Calls" --> FastAPIContainer
    FastAPIContainer -- "TCP" --> PostgresContainer
```

---

## 5. UI Flow Diagram (Screen Map)

### Narrative Explanation
**How does a user navigate the app?** This is a map of every screen in the application.
*   **The Starting Point**: Everyone starts at "Public Access". You Log In, and the system checks your role: "Are you a Teacher or a Student?".
*   **The Teacher's Path (Top Path)**: If you are a teacher, you go to the **Dashboard**. From there, you have three main jobs:
    1.  **Create Content**: Go to `My Courses` -> `Create Course` -> `AI Exam Generator`.
    2.  **Monitor**: Go to `Exams List` -> `Exam Review` to see grades.
    3.  **Analyze**: Use tools like `Cheating Detection` or `Pending Reviews`.
*   **The Student's Path (Bottom Path)**: If you are a student, your view is simpler. You go to `My Learning`. You find a course (`Browse Courses`), see the list of exams (`Course Exams`), and then—crucially—the system asks a question: **"Is the Exam Active?"**.
    *   If **No** (too early or too late): You are blocked.
    *   If **Yes**: You enter the `Take Exam Interface`.
*   **Significance**: This diagram proves we have considered the user experience (UX) and security constraints (active time checks) before writing the code.

### Mermaid Code
```mermaid
graph LR
    %% Styles
    classDef start fill:#2d3748,stroke:#1a202c,color:#fff,rx:5px,ry:5px;
    classDef page fill:#ebf8ff,stroke:#4299e1,stroke-width:2px,rx:5px,ry:5px;
    classDef subpage fill:#e6fffa,stroke:#38b2ac,stroke-width:1px,rx:5px,ry:5px;
    classDef decision fill:#fffaf0,stroke:#ed8936,stroke-width:2px,rx:50%;
    classDef action fill:#edf2f7,stroke:#a0aec0,stroke-width:1px,stroke-dasharray: 5 5;

    %% ---------------------------------------------------------
    %% PUBLIC ACCESS
    %% ---------------------------------------------------------
    subgraph Public ["1. Public Access"]
        Start(("Start")):::start
        LoginUI["Log In"]:::page
        RegUI["Sign Up"]:::page
        RoleCheck{{"User Role?"}}:::decision

        Start --> LoginUI
        LoginUI -- "New User" --> RegUI
        RegUI -- "Registered" --> LoginUI
        LoginUI -- "Success" --> RoleCheck
    end

    %% ---------------------------------------------------------
    %% TEACHER PORTAL
    %% ---------------------------------------------------------
    subgraph Teacher ["2. Teacher Portal"]
        T_Dash["Overview (Dashboard)"]:::start

        %% Course Module
        T_Courses["My Courses"]:::page
        T_NewCourse["Create Course"]:::subpage
        T_CourseDetail["Course Details"]:::subpage
        
        %% Exam Generation
        T_Generate["AI Exam Generator"]:::subpage

        %% Exam List & Details
        T_Exams["Exams List"]:::page
        T_ExamDetail["Exam Review"]:::subpage

        %% Other Modules
        T_Bulk["Bulk Upload"]:::page
        T_Plag["Cheating Detection"]:::page
        T_Review["Pending Reviews"]:::page

        %% Connections
        RoleCheck -- "Teacher" --> T_Dash
        
        T_Dash --> T_Courses
        T_Courses --> T_NewCourse
        T_Courses --> T_CourseDetail
        T_CourseDetail --> T_Generate
        
        T_Dash --> T_Exams
        T_Exams --> T_ExamDetail
        
        T_Dash --> T_Bulk
        T_Dash --> T_Plag
        T_Dash --> T_Review
    end

    %% ---------------------------------------------------------
    %% STUDENT PORTAL
    %% ---------------------------------------------------------
    subgraph Student ["3. Student Portal"]
        S_Dash["My Learning (Dashboard)"]:::start

        %% Course Module
        S_Courses["Browse Courses"]:::page
        S_ExamList["Course Exams"]:::subpage

        %% Exam Taking
        IsActive{{"Exam Active?"}}:::decision
        S_TakeExam["Take Exam Interface"]:::subpage

        %% Results
        S_Results["My Results"]:::page

        %% Connections
        RoleCheck -- "Student" --> S_Dash
        
        S_Dash --> S_Courses
        S_Courses --> S_ExamList
        S_ExamList --> IsActive
        IsActive -- "Yes" --> S_TakeExam
        
        S_Dash --> S_Results
    end
```

---

## 6. System Container Diagram (Strict)

### Narrative Explanation
This diagram is the "Source of Truth" for the system boundary. It removes any theoretical components (like Redis) and shows exactly what is running:
*   **Web App**: Next.js frontend.
*   **API**: FastAPI backend.
*   **Data**: Postgres + File Storage.
*   **External**: OpenAI (GPT-4o + Vision).

### Mermaid Code
```mermaid
graph TD
    %% CONTAINERS
    subgraph System ["AI Hybrid Assessment System"]
        WebApp["Web Application<br/>(React/Next.js)"]
        API["Backend API<br/>(FastAPI/Python)"]
    end

    %% DATA LAYER
    subgraph Data ["Data Layer"]
        PgSQL[("PostgreSQL<br/>(Relational + pgvector)")]
        FileStore[("File Storage<br/>(Local/S3)")]
    end

    %% EXTERNAL SERVICES
    subgraph External ["External Services"]
        OpenAI["OpenAI API<br/>(GPT-4o & Vision)"]
    end

    %% ACTORS
    Teacher["Teacher"]
    Student["Student"]

    %% FLOWS
    Teacher & Student -->|"HTTPS/JSON"| WebApp
    WebApp -->|"REST API"| API
    API -->|"SQL Query / Semantic Search"| PgSQL
    API -->|"Read/Write Artifacts"| FileStore
    API -->|"Generation / Vision / Grading"| OpenAI
```

---

## 7. Exam Engine Diagram (Ingestion & Generation)

### Narrative Explanation
Details the **Producer** workflow.
*   **Ingest**: PDF -> Parser -> Vector Store (Postgres).
*   **Generate**: Request -> RAG -> OpenAI -> Draft Exam.

### Mermaid Code
```mermaid
graph TD
    %% ACTORS
    Teacher["Teacher"]

    %% BACKEND COMPONENTS
    subgraph Backend ["Backend API"]
        Ingest["Material Ingestion<br/>(PDF Parser)"]
        RAG["RAG Engine<br/>(Vector Search)"]
        Gen["Exam Generator<br/>(LLM Prompter)"]
        Editor["Exam Editor Service"]
    end

    %% DATA 
    subgraph DB ["PostgreSQL"]
        Vectors[("Vector Store<br/>(Chunks)")]
        Exams[("Exam Tables<br/>(Drafts)")]
    end
    FileStore[("File Storage")]
    GPT["OpenAI GPT-4o"]

    %% FLOWS
    Teacher -->|"1. Upload PDF"| Ingest
    Ingest -->|"2. Store Raw File"| FileStore
    Ingest -->|"3. Chunk & Embed"| Vectors
    
    Teacher -->|"4. Request Exam"| Gen
    Gen -->|"5. Search Relevant Chunks"| Vectors
    Gen -->|"6. Prompt with Context"| GPT
    GPT -->|"7. Return Questions"| Gen
    Gen -->|"8. Save Draft"| Exams
    
    Teacher -->|"9. Edit & Publish"| Editor
    Editor -->|"10. Update Record"| Exams
```

---

## 8. Assessment Engine Diagram (Online Grading)

### Narrative Explanation
Details the **Online** workflow.
*   **Autosave**: Client -> API -> DB (Draft).
*   **Grading**: Submit -> AI Service -> Grades.
*   **Review**: Teacher Override -> Audit Logs.

### Mermaid Code
```mermaid
graph TD
    %% ACTORS
    Student["Student"]
    Teacher["Teacher"]

    %% BACKEND
    subgraph Backend ["Backend API"]
        Submission["Submission Service"]
        Grading["Grading Service<br/>(AI)"]
        Review["Review Service"]
    end

    %% DATA
    subgraph DB ["PostgreSQL"]
        Answers[("Student Answers")]
        Grades[("Evaluations")]
        Logs[("Audit Logs")]
    end
    GPT["OpenAI GPT-4o"]

    %% FLOWS
    Student -->|"1. Autosave Draft"| Submission
    Submission -->|"2. Update Record"| Answers
    Student -->|"3. Final Submit"| Submission
    Submission -->|"4. Lock Answer"| Answers
    
    Answers -->|"5. Trigger Grading"| Grading
    Grading -->|"6. Eval Request"| GPT
    Grading -->|"7. Save Score"| Grades
    
    Teacher -->|"8. Override Grade"| Review
    Review -->|"9. Update Score"| Grades
    Review -->|"10. Log Action"| Logs
```


---

## 8. Offline OCR & Mapping Diagram (Crucial)

### Narrative Explanation
Details the **Offline** capability using **OpenAI Vision**.
*   **Vision**: Image -> Text.
*   **Mapper**: Text + Student List -> LLM Fuzzy Match -> Mapped Answer.

### Mermaid Code
```mermaid
graph TD
    %% ACTORS
    Teacher["Teacher"]

    %% BACKEND
    subgraph Backend ["Backend API"]
        Upload["Bulk Upload Service"]
        Vision["OCR Service<br/>(OpenAI Vision)"]
        Mapper["Student Mapping Logic<br/>(LLM-based)"]
        Grader["Grading Service"]
    end

    %% DATA
    subgraph DB ["PostgreSQL"]
        Students[("User/Enrollment Tables")]
        Answers[("Student Answer Tables")]
    end
    FileStore[("File Storage")]
    GPT["OpenAI GPT-4o"]

    %% FLOWS
    Teacher -->|"1. Upload Scans"| Upload
    Upload -->|"2. Save Images"| FileStore
    Upload -->|"3. Transcribe Image"| Vision
    Vision -->|"4. Send Image"| GPT
    GPT -->|"5. Return Text"| Vision
    
    Vision -->|"6. Full Text"| Mapper
    Mapper -->|"7. Fetch Student List"| Students
    Students -.->|"8. Return List"| Mapper
    Mapper -->|"9. Match & Store Answer"| Answers
    
    Answers -->|"10. Trigger Grading"| Grader
```

