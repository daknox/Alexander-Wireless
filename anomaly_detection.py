"""
Anomaly Detection in Telecom Billing Data for Alexander Wireless
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: End-to-end anomaly detection engine for simulated telecom billing data. 
"""

import pandas as pd
import numpy as np
import os
import sys
import glob
import re

# ---------------------------
# 1. Data Loading
# ---------------------------
def load_sample_billing_data(filepath=None):
    """
    Load the sample billing cycle Excel file (all sheets concatenated).
    If no filepath is provided, load the latest Sample_Billing_Cycle_*.xlsx from data/sample_data/.
    Returns: df, mm_cc_yyyy_str (for output naming)
    """
    if filepath is None:
        files = glob.glob(os.path.join("data", "sample_data", "Sample_Billing_Cycle_*.xlsx"))
        if not files:
            raise FileNotFoundError("No sample billing cycle files found in data/sample_data/.")
        filepath = max(files, key=os.path.getctime)
        print(f"No file specified. Using latest sample: {filepath}")
    else:
        print(f"Loading file: {filepath}")
    # Extract mm-cc-yyyy from filename
    match = re.search(r"Sample_Billing_Cycle_(\d{2}-\d-\d{4})", os.path.basename(filepath))
    mm_cc_yyyy = match.group(1) if match else "cycle"
    # Read all sheets and concatenate
    all_sheets = pd.read_excel(filepath, sheet_name=None)
    df = pd.concat(all_sheets.values(), ignore_index=True)
    return df, mm_cc_yyyy

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
# 5. Join Code Descriptions (for anomalies only)
# ---------------------------
def join_code_descriptions(anomalies_df):
    desc_dir = os.path.join("data", "descriptions")
    sec_desc = pd.read_excel(os.path.join(desc_dir, "Single_Event_Charges_Descriptions.xlsx"))
    acr_desc = pd.read_excel(os.path.join(desc_dir, "Account_Corrections_Descriptions.xlsx"))
    sec_desc = sec_desc.rename(columns={"Billing_CODE": "Billing_CODE", "Billing Code Description": "SEC_Description"})
    acr_desc = acr_desc.rename(columns={"Billing_CODE": "Billing_CODE", "Billing Code Description": "ACR_Description"})

    # Merge SEC descriptions
    anomalies_df = anomalies_df.merge(sec_desc, on="Billing_CODE", how="left")
    # Merge ACR descriptions
    anomalies_df = anomalies_df.merge(acr_desc, on="Billing_CODE", how="left")

    # Fill Billing Code Description based on Bill_TYPE
    anomalies_df["Billing Code Description"] = anomalies_df.apply(
        lambda row: row["SEC_Description"] if row["Bill_TYPE"] == "SEC" else (
            row["ACR_Description"] if row["Bill_TYPE"] == "ACR" else row["Billing Code Description"]
        ), axis=1
    )
    # Drop helper columns
    anomalies_df = anomalies_df.drop(columns=["SEC_Description", "ACR_Description"])
    return anomalies_df

# ---------------------------
# 6. Output Results
# ---------------------------
def output_results(df, mm_cc_yyyy):
    import openpyxl
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import numbers

    output_dir = os.path.join("data", "Anomalies")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    anomalies = df[df["Anomaly"]].copy()
    anomalies = join_code_descriptions(anomalies)

    # Move 'Billing Code Description' to the end
    if 'Billing Code Description' in anomalies.columns:
        cols = [c for c in anomalies.columns if c != 'Billing Code Description'] + ['Billing Code Description']
        anomalies = anomalies[cols]

    anomaly_file_xlsx = os.path.join(output_dir, f"Anomalies_{mm_cc_yyyy}.xlsx")

    # Write to Excel with formatting
    with pd.ExcelWriter(anomaly_file_xlsx, engine="openpyxl") as writer:
        anomalies.to_excel(writer, index=False, sheet_name="Anomalies")
        ws = writer.sheets["Anomalies"]
        # Find columns to format
        percent_cols = [i+1 for i, c in enumerate(anomalies.columns) if 'Pct_' in c or 'Percent' in c]
        currency_cols = [i+1 for i, c in enumerate(anomalies.columns) if (
            c == 'Active Month' or c == 'Rolling_Avg' or c == 'Active_vs_Avg' or c == 'MoM_Change' or c.endswith('_Months_ago'))]
        # Apply formatting (skip header row)
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for idx in percent_cols:
                cell = row[idx-1]
                cell.number_format = '0.00%'
            for idx in currency_cols:
                cell = row[idx-1]
                cell.number_format = '[$$-409]#,##0.00'
    print(f"Anomaly report saved to: {anomaly_file_xlsx}")

# ---------------------------
# 7. Main Execution
# ---------------------------
if __name__ == "__main__":
    # Accept file path as argument
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    df, mm_cc_yyyy = load_sample_billing_data(filepath)
    df = clean_data(df)
    df = calculate_rolling_average(df)
    df = calculate_deltas(df)
    df = flag_special_cases(df)
    df = flag_anomalies(df)
    output_results(df, mm_cc_yyyy)
    print("Anomaly detection complete.") 