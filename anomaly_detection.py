"""
Anomaly Detection in Telecom Billing Data for Alexander Wireless
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: End-to-end anomaly detection engine for simulated telecom billing data. 
"""

import pandas as pd
import numpy as np

# ---------------------------
# 1. Data Simulation
# ---------------------------
def simulate_billing_data(n_rows=500):
    """
    Simulate telecom billing data with realistic structure.
    """
    np.random.seed(42)
    years = np.random.choice([2022, 2023], n_rows)
    months = np.random.choice(range(1, 13), n_rows)
    bill_cycles = np.random.choice(range(1, 4), n_rows)
    bill_types = np.random.choice([
        "Miscellaneous Charges", "Core Plan Charges", 
        "Feature Add-ons", "Account Reconciliations"
    ], n_rows)
    billing_codes = [f"C{str(i).zfill(3)}" for i in np.random.choice(range(1, 100), n_rows)]
    descriptions = [f"Description for {code}" for code in billing_codes]
    
    # Simulate 5 months of history + active month
    data = {
        "Year": years,
        "Month": months,
        "Bill Cycle Number": bill_cycles,
        "Bill_TYPE": bill_types,
        "Billing_CODE": billing_codes,
        "Billing Code Description": descriptions,
    }
    for i in range(5, 0, -1):
        data[f"{i}_Months_ago"] = np.random.gamma(100, 2, n_rows).round(2)
    data["Active Month"] = np.random.gamma(100, 2, n_rows).round(2)
    
    df = pd.DataFrame(data)
    # Randomly introduce some NaNs for realism
    for col in [f"{i}_Months_ago" for i in range(5, 0, -1)] + ["Active Month"]:
        df.loc[df.sample(frac=0.05).index, col] = np.nan
    return df

# ---------------------------
# 2. Data Cleaning
# ---------------------------
def clean_data(df):
    """
    Clean and preprocess the billing data.
    """
    # Ensure numeric columns are floats
    for col in [f"{i}_Months_ago" for i in range(5, 0, -1)] + ["Active Month"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# ---------------------------
# 3. Feature Engineering
# ---------------------------
def calculate_rolling_average(df):
    """
    Calculate rolling average of previous 5 months for each row.
    """
    df["Rolling_Avg"] = df[[f"{i}_Months_ago" for i in range(5, 0, -1)]].mean(axis=1)
    return df

def calculate_deltas(df):
    """
    Calculate active vs avg, percent change, MoM change, etc.
    """
    df["Active_vs_Avg"] = df["Active Month"] - df["Rolling_Avg"]
    df["Pct_Change_Active_vs_Avg"] = df["Active_vs_Avg"] / df["Rolling_Avg"]
    df["MoM_Change"] = df["Active Month"] - df["1_Months_ago"]
    df["Pct_Change_MoM"] = df["MoM_Change"] / df["1_Months_ago"]
    return df

def flag_special_cases(df):
    """
    Flag drop to 0 and new code cases.
    """
    df["Drop_to_0"] = df.apply(
        lambda row: (row["Active Month"] == 0 or pd.isna(row["Active Month"])) and
                    any([not pd.isna(row[f"{i}_Months_ago"]) for i in range(5, 0, -1)]),
        axis=1
    )
    df["New_Code"] = df.apply(
        lambda row: all([pd.isna(row[f"{i}_Months_ago"]) for i in range(5, 0, -1)]) and
                    not pd.isna(row["Active Month"]),
        axis=1
    )
    return df

# ---------------------------
# 4. Anomaly Detection Logic
# ---------------------------
def flag_anomalies(df, z_thresh=2.5, pct_thresh=0.5):
    """
    Flag anomalies based on z-score and percent change.
    """
    # Z-score for Active_vs_Avg
    df["Active_vs_Avg_z"] = (df["Active_vs_Avg"] - df["Active_vs_Avg"].mean()) / df["Active_vs_Avg"].std()
    df["Anomaly"] = (
        (df["Active_vs_Avg_z"].abs() > z_thresh) |
        (df["Pct_Change_Active_vs_Avg"].abs() > pct_thresh) |
        (df["Drop_to_0"]) |
        (df["New_Code"])
    )
    return df

# ---------------------------
# 5. Summary Statistics
# ---------------------------
def generate_summary_statistics(df):
    """
    Generate summary statistics for the dataset.
    """
    summary = {
        "Total Rows": len(df),
        "Anomalies Detected": int(df["Anomaly"].sum()),
        "Drop to 0 Cases": int(df["Drop_to_0"].sum()),
        "New Codes": int(df["New_Code"].sum()),
        "Mean Active_vs_Avg": df["Active_vs_Avg"].mean(),
        "Std Active_vs_Avg": df["Active_vs_Avg"].std(),
    }
    return summary

# ---------------------------
# 6. Main Execution
# ---------------------------
if __name__ == "__main__":
    # Simulate data
    df = simulate_billing_data()
    df = clean_data(df)
    df = calculate_rolling_average(df)
    df = calculate_deltas(df)
    df = flag_special_cases(df)
    df = flag_anomalies(df)
    summary = generate_summary_statistics(df)
    
    print("Summary Statistics:")
    for k, v in summary.items():
        print(f"{k}: {v}")
    # Optionally: df.to_csv("anomaly_output.csv", index=False) 