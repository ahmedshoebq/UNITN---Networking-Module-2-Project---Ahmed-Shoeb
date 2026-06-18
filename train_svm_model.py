import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import time
 
# -------------------------------------------------
# 1. Load dataset
# -------------------------------------------------
DATA_FILE = "traffic_data.csv"
raw = pd.read_csv(DATA_FILE)
print(f"Raw shape: {raw.shape}")
print("Columns:", list(raw.columns))
print(raw.head())
 
data = raw.copy()
 
# -------------------------------------------------
# 2. Clean dataset
# -------------------------------------------------
before = len(data)
data = data[data["port"] != 4294967294]
print(f"\nRemoved {before - len(data)} mgmt-port rows")
 
for col in ["rx_bytes", "tx_bytes", "port", "datapath"]:
    data[col] = pd.to_numeric(data[col], errors="coerce")
data = data.dropna().reset_index(drop=True)
 
data["timestamp"] = pd.to_datetime(data["timestamp"], format="%H:%M:%S")
data = data.sort_values(["datapath", "port", "timestamp"]).reset_index(drop=True)
 
data["rx_rate"] = data.groupby(["datapath", "port"])["rx_bytes"].diff()
data["tx_rate"] = data.groupby(["datapath", "port"])["tx_bytes"].diff()
 
data = data.dropna(subset=["rx_rate", "tx_rate"])
data = data[(data["rx_rate"] >= 0) & (data["tx_rate"] >= 0)]
data = data.reset_index(drop=True)
data["time_index"] = range(len(data))
 
print(f"Cleaned dataset: {data.shape}")
 
# -------------------------------------------------
# 3. Features and target
# -------------------------------------------------
data["rx_rate_lag1"] = data.groupby(["datapath", "port"])["rx_rate"].shift(1)
data["tx_rate_lag1"] = data.groupby(["datapath", "port"])["tx_rate"].shift(1)
data = data.dropna().reset_index(drop=True)
 
feature_cols = ["rx_rate_lag1", "tx_rate_lag1", "tx_rate", "port", "datapath"]
target_col   = "rx_rate"
 
X = data[feature_cols]
y = data[target_col]
 
print(f"\nTarget stats (original):")
print(f"  Mean : {y.mean():.2f} bytes/interval")
print(f"  Max  : {y.max():.2f}")
print(f"  Std  : {y.std():.2f}")
 
# -------------------------------------------------
# Log transform — fixes SVR by squashing extreme values
# np.log1p = log(1 + x) which safely handles zeros
# Example: 9,000,000,000 becomes 23.9 instead of 9 billion
#          0             becomes 0.0  instead of 0
# -------------------------------------------------
y_log = np.log1p(y)
X_log = X.copy()
X_log["rx_rate_lag1"] = np.log1p(X["rx_rate_lag1"])
X_log["tx_rate_lag1"] = np.log1p(X["tx_rate_lag1"])
X_log["tx_rate"]      = np.log1p(X["tx_rate"])
 
print(f"\nTarget stats (after log transform):")
print(f"  Mean : {y_log.mean():.4f}")
print(f"  Max  : {y_log.max():.4f}")
print(f"  Std  : {y_log.std():.4f}")
print(f"  (values now on a manageable scale for SVR)")
 
X_train, X_test, y_train, y_test = train_test_split(
    X_log, y_log, test_size=0.3, random_state=42
)
 
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
 
print(f"\nTraining rows : {len(X_train)}")
print(f"Test rows     : {len(X_test)}")
 
# -------------------------------------------------
# 4. Train and compare all four models
# -------------------------------------------------
models = {
    "LinearRegression": LinearRegression(),
    "DecisionTree":     DecisionTreeRegressor(max_depth=6, random_state=42),
    "RandomForest":     RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42),
    "SVR":              SVR(kernel="rbf", C=100, gamma="scale", epsilon=0.01),
}
 
results = []
print("\n--- Training models ---")
for name, model in models.items():
    start      = time.time()
    model.fit(X_train_scaled, y_train)
    y_pred_log = model.predict(X_test_scaled)
    dur        = time.time() - start
 
    # R2 on log scale
    r2_log = r2_score(y_test, y_pred_log)
 
    # MAE converted back to original bytes scale
    y_pred_orig = np.expm1(y_pred_log)
    y_test_orig = np.expm1(y_test)
    mae_orig    = mean_absolute_error(y_test_orig, y_pred_orig)
 
    results.append([name, mae_orig, r2_log, dur])
    print(f"  {name:<20} MAE={mae_orig:>15,.0f}  R2={r2_log:.4f}  ({dur:.3f}s)")
 
# -------------------------------------------------
# 5. Print comparison table
# -------------------------------------------------
print("\n" + "=" * 65)
print("Model comparison — traffic_data.csv (log-transformed rx_rate)")
print("=" * 65)
print("{:<20} {:<18} {:<10} {:<10}".format("Model", "MAE (bytes)", "R2", "Train(s)"))
print("-" * 65)
for r in results:
    print("{:<20} {:<18,.0f} {:<10.4f} {:<10.3f}".format(*r))
print("=" * 65)
 
best = min(results, key=lambda x: x[1])
print(f"\nBest model by MAE : {best[0]}")
print(f"  MAE  = {best[1]:,.0f} bytes/interval")
print(f"  R2   = {best[2]:.4f}")
 
print("\nNote: R2 measured on log scale.")
print("      MAE converted back to original bytes scale.")
 
# -------------------------------------------------
# 6. Save results
# -------------------------------------------------
results_df = pd.DataFrame(results, columns=["Model", "MAE", "R2", "TrainTime"])
results_df.to_csv("model_comparison_results.csv", index=False)
print("\nSaved model_comparison_results.csv")
print("\n=== Model comparison finished ===")