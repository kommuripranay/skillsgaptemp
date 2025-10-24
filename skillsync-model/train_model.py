import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import time

# --- 1. LOAD THE LABELED DATA ---
print("Loading v1_labeled_dataset.csv...")
try:
    data = pd.read_csv("v1_labeled_dataset.csv")
except FileNotFoundError:
    print("❌ ERROR: v1_labeled_dataset.csv not found.")
    print("Please make sure it's in the same folder as this script.")
    exit()

print(f"Loaded {len(data)} rows of data.")

# --- 2. PRE-PROCESS THE DATA ---
# A machine learning model can't read text like "React" or "Tier 1".
# We must convert all our text columns into numbers.
# "One-Hot Encoding" turns a column like 'company_tier' into:
# 'company_tier_Tier 1', 'company_tier_Tier 2', 'company_tier_Tier 3'
# with 1s and 0s.

print("Pre-processing data (One-Hot Encoding)...")

# Define which columns are our 'features' (X) and 'target' (y)
y = data['target_score']
# We drop 'target_score' (it's the answer) and 'job_id' (it's just an ID)
X = data.drop(['target_score', 'job_id'], axis=1)

# pd.get_dummies() automatically converts all text columns into numbers
X_processed = pd.get_dummies(X, columns=['skill_name', 'context_keywords', 'company_tier'])

# Convert 'is_required' from True/False to 1/0
X_processed['is_required'] = X_processed['is_required'].astype(int)

print(f"Data converted into {X_processed.shape[1]} features.")

# --- 3. SPLIT DATA FOR TRAINING AND TESTING ---
# We use 80% of data to train the model and 20% to test how accurate it is.
# random_state=42 ensures we get the same "random" split every time.
X_train, X_test, y_train, y_test = train_test_split(
    X_processed, 
    y, 
    test_size=0.2, 
    random_state=42
)

print(f"Splitting data: {len(X_train)} rows for training, {len(X_test)} rows for testing.")

# --- 4. TRAIN THE "MODEL 2" (Random Forest) ---
print("Training Model 2 (RandomForestRegressor)...")
start_time = time.time()

# n_estimators=100 means it builds 100 "decision trees" (a good default).
# random_state=42 ensures the model is built the same way every time.
# n_jobs=-1 uses all your computer's CPU cores to train faster.
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

end_time = time.time()
print(f"✅ Model trained successfully in {end_time - start_time:.2f} seconds.")

# --- 5. EVALUATE THE MODEL ---
print("Evaluating model performance...")
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)

print("\n--- MODEL EVALUATION ---")
print(f"Mean Absolute Error (MAE): {mae:.2f} points")
print(f"--- This means, on average, our new model's score prediction is off by ~{mae:.0f} points. ---")
if mae < 50:
    print("--- 🎯 This is a great score! ---")
else:
    print("--- This is a good start. We can improve it by refining our heuristic rules. ---")


# --- 6. SAVE THE MODEL ---
# We save the trained model and the list of feature columns to files.
# These two files ARE "Model 2". We'll need them in production.
print("\nSaving model to disk...")

# Save the model itself
joblib.dump(model, "skill_sync_model.joblib")

# Save the list of columns. This is CRITICAL.
# We need this to ensure any *new* data is encoded in the exact same order.
model_columns = list(X_processed.columns)
joblib.dump(model_columns, "model_columns.joblib")

print("✅ Model and columns saved as:")
print("1. skill_sync_model.joblib")
print("2. model_columns.joblib")
print("\nAll done!")