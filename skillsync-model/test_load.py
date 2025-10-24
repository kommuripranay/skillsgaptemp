import joblib

print("Loading the model and its columns...")

# Load the two files we saved
try:
    model = joblib.load("skill_sync_model.joblib")
    columns = joblib.load("model_columns.joblib")

    print("✅ Success! Model loaded.")
    print("\n--- Model Info ---")
    print(model)
    
    print(f"\nModel was trained with {len(columns)} features.")
    print("First 5 features:", columns[:5])

except FileNotFoundError:
    print("❌ ERROR: Could not find model files.")
    print("Make sure 'skill_sync_model.joblib' and 'model_columns.joblib' are in the same folder.")
except Exception as e:
    print(f"An error occurred: {e}")