import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib

# 1. Load your synthetic data
print("Loading data...")
df = pd.read_csv("olive_jam_dataset.csv")

# 2. Split into "Features" (Inputs) and "Targets" (Outputs)
X = df[['hopper_level', 'belt_speed', 'flow_rate', 'olives_weight']]

y_jam = df['label_jam_imminent']
y_intensity = df['vibrator_intensity']

# 3. Train the Models
print("Training AI Models...")
# Classifier for the Jam (True/False)
jam_model = RandomForestClassifier(n_estimators=50, random_state=42)
jam_model.fit(X, y_jam)

# Regressor for the Intensity (0 to 100)
intensity_model = RandomForestRegressor(n_estimators=50, random_state=42)
intensity_model.fit(X, y_intensity)

# 4. Save the "Brains" into a single file
models = {
    "jam_model": jam_model,
    "intensity_model": intensity_model
}

model_path = "olive_ai_models.pkl"
joblib.dump(models, model_path)
print(f"✅ Training Complete! AI saved to '{model_path}'")