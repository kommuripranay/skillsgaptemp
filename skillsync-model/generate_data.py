import csv
import random

# --- 1. DEFINE YOUR SKILL TAXONOMY ---
# (We can expand this list later)

SKILL_CLUSTERS = {
    "frontend": ["React", "JavaScript", "TypeScript", "HTML", "CSS", "Tailwind CSS", "Vue.js"],
    "backend_python": ["Python", "Django", "Flask", "FastAPI", "SQL", "PostgreSQL", "MongoDB"],
    "backend_java": ["Java", "Spring Boot", "Kotlin", "SQL", "Oracle", "Microservices"],
    "backend_node": ["Node.js", "Express.js", "TypeScript", "PostgreSQL", "MongoDB", "GraphQL"],
    "devops": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", "Jenkins"],
    "data_science": ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "SQL", "Tableau"],
    "core_cs": ["Data Structures", "Algorithms", "System Design", "OOP"],
    "soft_skills": ["Communication", "Problem-solving", "Leadership", "Mentoring", "Teamwork", "Accountability"]
}

COMPANY_TIERS = ["Tier 1", "Tier 2", "Tier 3"]

# --- 2. DEFINE JOB ARCHETYPES ---
# This makes the data realistic. A "Senior" job will have different skills
# and experience requirements than a "Junior" job.

JOB_ARCHETYPES = {
    "junior_frontend": {
        "clusters": ["frontend", "soft_skills"],
        "years_range": (0, 2),
        "context_keywords": ["Junior", "Familiar", "None"],
        "skills_per_job": (3, 5)
    },
    "mid_backend_python": {
        "clusters": ["backend_python", "devops", "core_cs", "soft_skills"],
        "years_range": (2, 5),
        "context_keywords": ["Familiar", "None", "Senior"],
        "skills_per_job": (4, 7)
    },
    "senior_frontend": {
        "clusters": ["frontend", "core_cs", "soft_skills"],
        "years_range": (5, 10),
        "context_keywords": ["Senior", "Expert", "Lead", "None"],
        "skills_per_job": (5, 8)
    },
    "lead_devops": {
        "clusters": ["devops", "backend_python", "core_cs", "soft_skills"],
        "years_range": (8, 15),
        "context_keywords": ["Lead", "Expert", "Architect"],
        "skills_per_job": (6, 10)
    },
    "junior_data_scientist": {
        "clusters": ["data_science", "soft_skills"],
        "years_range": (0, 3),
        "context_keywords": ["Junior", "Familiar", "None"],
        "skills_per_job": (4, 6)
    },
    "senior_java_dev": {
        "clusters": ["backend_java", "devops", "core_cs", "soft_skills"],
        "years_range": (6, 12),
        "context_keywords": ["Senior", "Expert", "None"],
        "skills_per_job": (5, 8)
    }
}

def generate_mock_data(num_jobs, filename="mock_skill_data.csv"):
    """
    Generates a CSV file with mock skill data from a number of simulated jobs.
    """
    
    # These are the columns you specified
    header = ['job_id', 'skill_name', 'years_required', 'context_keywords', 'is_required', 'company_tier']
    
    # We will store all our skill rows here
    all_skill_rows = []
    
    print(f"Generating data for {num_jobs} simulated jobs...")

    for i in range(num_jobs):
        job_id = 1000 + i
        company_tier = random.choice(COMPANY_TIERS)
        
        # 1. Pick a random job archetype
        archetype_name = random.choice(list(JOB_ARCHETYPES.keys()))
        archetype = JOB_ARCHETYPES[archetype_name]
        
        # 2. Get the settings for this job
        min_years, max_years = archetype["years_range"]
        min_skills, max_skills = archetype["skills_per_job"]
        num_skills_for_this_job = random.randint(min_skills, max_skills)
        
        # 3. Create a "skill pool" for this job to pick from
        skill_pool = []
        for cluster_name in archetype["clusters"]:
            skill_pool.extend(SKILL_CLUSTERS[cluster_name])
        
        # 4. Generate the skill rows for this single job
        skills_added = set() # To avoid duplicate skills for the same job
        
        for _ in range(num_skills_for_this_job):
            skill_name = random.choice(skill_pool)
            
            # Skip if we already added this skill for this job
            if skill_name in skills_added:
                continue
            
            skills_added.add(skill_name)
            
            # Generate realistic features
            years_required = random.randint(min_years, max_years)
            context_keywords = random.choice(archetype["context_keywords"])
            
            # Make "true" more likely for is_required
            is_required = random.choices([True, False], weights=[0.7, 0.3], k=1)[0]
            
            # Clean up logic: a "Bonus" or "Familiar" skill likely isn't "required"
            if context_keywords in ["Familiar", "Bonus"]:
                is_required = False
            
            # Clean up logic: A "Junior" skill likely doesn't require 8 years
            if context_keywords == "Junior":
                years_required = random.randint(0, 2)
            
            # Clean up logic: An "Expert" skill likely needs more than 1 year
            if context_keywords in ["Expert", "Lead", "Senior", "Architect"]:
                years_required = random.randint(max(3, min_years), max_years)

            # Add the new row
            all_skill_rows.append({
                'job_id': job_id,
                'skill_name': skill_name,
                'years_required': years_required,
                'context_keywords': context_keywords,
                'is_required': is_required,
                'company_tier': company_tier
            })

    # 5. Write all the generated rows to the CSV file
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()
            writer.writerows(all_skill_rows)
        
        print(f"\n✅ Success! {len(all_skill_rows)} rows written to {filename}")
        
    except IOError as e:
        print(f"\n❌ Error writing to file: {e}")

# --- 3. RUN THE SCRIPT ---
if __name__ == "__main__":
    # Change this number to generate more or fewer *jobs*.
    # 2000 jobs will create around 10,000 - 14,000 skill rows.
    NUMBER_OF_JOBS_TO_SIMULATE = 2000
    generate_mock_data(NUMBER_OF_JOBS_TO_SIMULATE)