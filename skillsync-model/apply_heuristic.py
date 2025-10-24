import csv

# ===================================================================
# PART 1: THE HEURISTIC MODEL (THE "RULEBOOK")
# ===================================================================

def get_heuristic_score(skill_row):
    """
    This is our v1 Heuristic Model (The Rulebook).
    It takes a dictionary (a row from our CSV) and returns a score from 0-1000.
    """
    
    # Get the features from the row and clean them
    skill_name = skill_row['skill_name']
    years = int(skill_row['years_required'])
    context = skill_row['context_keywords']
    # Convert the string 'True' or 'False' into an actual Boolean
    is_required = skill_row['is_required'] == 'True' 
    tier = skill_row['company_tier']

    # A list of our defined soft skills to treat them differently
    SOFT_SKILLS = ["Communication", "Problem-solving", "Leadership", "Mentoring", "Teamwork", "Accountability"]

    # --- RULE 1: SPECIAL LOGIC FOR SOFT SKILLS ---
    # These are scored differently than tech skills.
    if skill_name in SOFT_SKILLS:
        if skill_name in ["Leadership", "Mentoring", "Accountability"]:
            return 750  # High-level senior/lead skill
        elif skill_name == "Problem-solving":
            return 600  # Mid-to-Senior level skill
        else:
            return 400  # Core skill for all levels

    # --- RULE 2: BASE SCORE FROM YEARS OF EXPERIENCE ---
    # This is our starting point for all technical skills.
    base_score = 0
    if years >= 8:
        base_score = 800  # Senior / Lead
    elif years >= 5:
        base_score = 650  # Senior
    elif years >= 3:
        base_score = 500  # Mid-level
    elif years >= 1:
        base_score = 300  # Junior
    else:
        base_score = 150  # Entry-level / Familiarity

    # --- RULE 3: ADJUST SCORE BASED ON CONTEXT KEYWORDS ---
    # Keywords are powerful modifiers that add or subtract points.
    if context in ["Expert", "Lead", "Architect", "Senior"]:
        base_score = max(base_score, 600)  # Set a minimum score of 600
        base_score += 150  # Add a big bonus
    elif context == "Familiar":
        base_score -= 150  # Subtract points for "familiarity"
    elif context == "Junior":
        base_score = min(base_score, 350)  # Cap the score
    elif context == "Bonus":
        base_score = min(base_score, 250)  # Cap at a low score (nice-to-have)

    # --- RULE 4: ADJUST SCORE BASED ON REQUIREMENT ---
    if is_required:
        base_score += 50  # Give a small bonus if it's a "must-have"
    else:
        # If it's not required AND has no context, it's just a "nice-to-have"
        if context == "None":
            base_score -= 100

    # --- RULE 5: ADJUST SCORE BASED ON COMPANY TIER ---
    # A small adjustment. A Tier 1 company might have higher standards.
    if tier == "Tier 1":
        base_score += 25
    elif tier == "Tier 3":
        base_score -= 25

    # --- RULE 6: FINALIZE THE SCORE (CLIPPING) ---
    # Ensure the final score is always between 0 and 1000.
    final_score = max(0, min(base_score, 1000))
    
    return int(final_score)

# ===================================================================
# PART 2: THE "WORKER" SCRIPT
# ===================================================================

def process_data(input_file, output_file):
    """
    Reads the mock data, applies the heuristic model to each row,
    and saves the new labeled data to a new CSV file.
    """
    print(f"Reading data from {input_file}...")
    
    labeled_data = []
    
    try:
        # Open the CSV you generated
        with open(input_file, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Loop through every row in that file
            for row in reader:
                # This is the magic line:
                # We apply our "Rulebook" (Model 1) to get a score
                score = get_heuristic_score(row)
                
                # Add the new score to the row
                row['target_score'] = score
                labeled_data.append(row)
        
        print(f"Processed {len(labeled_data)} rows.")

    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at {input_file}")
        print("Please make sure 'mock_skill_data.csv' is in the same folder.")
        return
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        return

    # --- Write the new data to the output file ---
    if labeled_data:
        # Get all column headers (including our new 'target_score')
        headers = labeled_data[0].keys()
        
        try:
            # Create the new CSV file
            with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(labeled_data)
            
            print(f"✅ Success! Labeled dataset saved to {output_file}")
            
        except IOError as e:
            print(f"❌ ERROR writing to file: {e}")

# ===================================================================
# PART 3: RUN THE SCRIPT
# ===================================================================

if __name__ == "__main__":
    INPUT_CSV = "mock_skill_data.csv"
    OUTPUT_CSV = "v1_labeled_dataset.csv"  # The new file we are creating
    process_data(INPUT_CSV, OUTPUT_CSV)