erDiagram
    auth.users ||--o{ profiles : "has one"
    
    profiles ||--o{ user_skill_supply : "has many"
    profiles ||--o{ user_assessment_attempts : "has many"

    skills ||--o{ user_skill_supply : "has many"
    skills ||--o{ job_skill_demand : "has many"
    skills ||--o{ assessments : "has many"

    assessments ||--o{ questions : "has many"
    assessments ||--o{ user_assessment_attempts : "has many"

    questions ||--o{ options : "has many"
    questions ||--o{ user_answers : "has many"

    user_assessment_attempts ||--o{ user_answers : "has many"
    
    options ||--o{ user_answers : "links to"

    %% --- Table Definitions ---

    auth.users {
        uuid id (PK)
        string email
        -- ... (more auth fields)
    }

    profiles {
        uuid id (PK, FK to auth.users.id)
        string full_name
        string email
        string avatar_url
    }

    skills {
        int id (PK)
        string name (Unique)
        string category "e.g., 'frontend', 'backend', 'soft-skill'"
    }

    job_skill_demand {
        int id (PK)
        string job_api_id "ID from Jooble/Adzuna"
        int skill_id (FK to skills.id)
        int demand_score "0-1000"
        string job_title
        string company_name
        string apply_url
        timestamp scraped_at
    }

    user_skill_supply {
        int id (PK)
        uuid user_id (FK to profiles.id)
        int skill_id (FK to skills.id)
        int supply_score "0-1000"
        string source_type "e.g., 'self-assessed', 'mcq', 'coding-challenge'"
        timestamp last_updated
        -- Unique constraint on (user_id, skill_id)
    }

    assessments {
        int id (PK)
        int skill_id (FK to skills.id)
        string title "e.g., 'React Core Concepts Quiz'"
        string type "e.g., 'mcq', 'coding-challenge'"
        string difficulty "e.g., 'easy', 'medium', 'hard'"
    }

    questions {
        int id (PK)
        int assessment_id (FK to assessments.id)
        string question_text
        string question_type "e.g., 'single-choice', 'multiple-choice'"
        string code_snippet (nullable)
    }

    options {
        int id (PK)
        int question_id (FK to questions.id)
        string option_text
        bool is_correct "True if this is a correct answer"
    }

    user_assessment_attempts {
        int id (PK)
        uuid user_id (FK to profiles.id)
        int assessment_id (FK to assessments.id)
        timestamp completed_at
        float final_grade_percentage
        int calculated_score "The 0-1000 score from this attempt"
    }

    user_answers {
        int id (PK)
        int attempt_id (FK to user_assessment_attempts.id)
        int question_id (FK to questions.id)
        int selected_option_id (FK to options.id)
        bool is_correct "Was this user's selection correct?"
    }