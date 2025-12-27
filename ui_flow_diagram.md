# AI Hybrid Assessment System - UI Flow Diagram (Screen Map)

**Goal**: Visualizing every single screen in the application and how they connect.

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

## Screen Definitions

### 1. Public Access
*   **Log In**: Entry point. Authenticates credentials.
*   **Sign Up**: Account creation.
*   **User Role?**: System logic that directs users based on their account type (Teacher vs Student).

### 2. Teacher Portal
*   **Overview**: Key statistics and recent activity.
*   **My Courses**: List of teaching subjects.
    *   **Course Details**: Upload materials (PDFs) and manage the course.
    *   **AI Exam Generator**: Configuration screen to create exams from course content.
*   **Exams List**: All scheduled and past exams.
    *   **Exam Review**: Detailed view of student performance and questions.
*   **Bulk Upload**: Offline exam processing (scan to grade).
*   **Cheating Detection**: Plagiarism analysis tool.
*   **Pending Reviews**: Queue for manual grading of low-confidence AI marks.

### 3. Student Portal
*   **My Learning**: Dashboard with "Upcoming" and "Missed" exams.
*   **Browse Courses**: Catalog of enrolled courses.
    *   **Course Exams**: List of tests available for a specific subject.
*   **Take Exam**: The timed testing environment.
*   **My Results**: History of grades and feedback.
