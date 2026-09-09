import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

print("Generating synthetic factory data...")

num_samples = 10000
np.random.seed(42)

base_weight = np.random.uniform(0, 100, num_samples)
friction = np.random.uniform(0, 50, num_samples)
final_weight = base_weight + friction  

mass_flow_rate = np.random.uniform(50, 120, num_samples)
# 50/50 split so AI gets plenty of data on the damaged state
vibrator_damage = np.random.choice([0, 1], num_samples, p=[0.5, 0.5]) 

# Timers up to 15 seconds to give sharp contrast around the 5.0 mark
time_jam = np.random.uniform(0, 15, num_samples) 
time_anomaly = np.random.uniform(0, 15, num_samples)
time_maintenance = np.random.uniform(0, 15, num_samples)

jam_label = np.zeros(num_samples, dtype=int)
anomaly_label = np.zeros(num_samples, dtype=int)
maintenance_label = np.zeros(num_samples, dtype=int)

for i in range(num_samples):
    # JAM
    if final_weight[i] < 50 and vibrator_damage[i] == 0 and time_jam[i] >= 5.0:
        jam_label[i] = 1
        
    # ANOMALY
    if final_weight[i] < 50 and vibrator_damage[i] == 1 and time_anomaly[i] >= 5.0:
        anomaly_label[i] = 1
            
    # MAINTENANCE
    if 90 <= base_weight[i] <= 100 and friction[i] > 20 and time_maintenance[i] >= 5.0:
        maintenance_label[i] = 1

df = pd.DataFrame({
    'final_weight': final_weight,
    'mass_flow_rate': mass_flow_rate,
    'vibrator_damage': vibrator_damage,
    'time_jam': time_jam,
    'time_anomaly': time_anomaly,
    'time_maintenance': time_maintenance,
    'friction': friction,
    'base_weight': base_weight,
    'anomaly': anomaly_label,
    'jam': jam_label,
    'maintenance': maintenance_label
})

print("Training AI Models...")
X = df[['final_weight', 'mass_flow_rate', 'vibrator_damage', 'time_jam', 'time_anomaly', 'time_maintenance', 'friction', 'base_weight']]

jam_model = RandomForestClassifier(n_estimators=50, random_state=42)
jam_model.fit(X, df['jam'])

maintenance_model = RandomForestClassifier(n_estimators=50, random_state=42)
maintenance_model.fit(X, df['maintenance'])

anomaly_model = RandomForestClassifier(n_estimators=50, random_state=42)
anomaly_model.fit(X, df['anomaly'])

models = {"jam_model": jam_model, "maintenance_model": maintenance_model, "anomaly_model": anomaly_model}

joblib.dump(models, 'smart_factory_ai.pkl')
print("✅ Models saved! AI 5-second thresholds are now perfectly sharp.")