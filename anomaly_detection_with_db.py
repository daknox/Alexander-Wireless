"""
Enhanced Anomaly Detection with Database Integration for Telecom Billing Data
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: End-to-end anomaly detection engine with SQLite database storage for all processed data.
"""

import pandas as pd
import numpy as np
import os
import sys
import glob
import re
import logging
from datetime import datetime
from database_integration import DatabaseIntegration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        logger.info(f"No file specified. Using latest sample: {filepath}")
    else:
        logger.info(f"Loading file: {filepath}")
        
    # Extract mm-cc-yyyy from filename
    match = re.search(r"Sample_Billing_Cycle_(\d{2}-\d-\d{4})", os.path.basename(filepath))
    mm_cc_yyyy = match.group(1) if match else "cycle"
    
    # Read all sheets and concatenate
    all_sheets = pd.read_excel(filepath, sheet_name=None)
    df = pd.concat(all_sheets.values(), ignore_index=True)
    
    return df, mm_cc_yyyy, filepath

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
# 6. Database Integration
# ---------------------------
def process_with_database(df, mm_cc_yyyy, file_path=None):
    """
    Process the data and store everything in the database.
    """
    # Initialize database integration
    db_integration = DatabaseIntegration()
    
    try:
        # Extract cycle information from mm_cc_yyyy
        parts = mm_cc_yyyy.split('-')
        month = int(parts[0])
        cycle_number = int(parts[1])
        year = int(parts[2])
        cycle_date = f"{year}-{month:02d}-01"
        
        # Create processing cycle
        cycle_id = db_integration.create_processing_cycle(
            cycle_date=cycle_date,
            cycle_number=cycle_number,
            year=year,
            month=month,
            file_path=file_path
        )
        
        logger.info(f"Created processing cycle {cycle_id} for {mm_cc_yyyy}")
        
        # Log processing start
        db_integration.log_processing_event(cycle_id, "Processing started", "INFO")
        
        # Store all billing data (including non-anomalies)
        records_stored = db_integration.store_billing_data(cycle_id, df)
        logger.info(f"Stored {records_stored} billing records in database")
        
        # Store detailed anomaly information
        anomalies_stored = db_integration.store_anomaly_details(cycle_id, df)
        logger.info(f"Stored {anomalies_stored} anomaly details in database")
        
        # Update processing cycle statistics
        db_integration.update_processing_cycle_stats(cycle_id)
        
        # Log processing completion
        db_integration.log_processing_event(cycle_id, "Processing completed successfully", "INFO")
        
        # Get and display summary
        summary = db_integration.get_cycle_summary(cycle_id)
        if summary:
            cycle_info = summary['cycle_info']
            logger.info(f"Processing Summary:")
            logger.info(f"  Cycle: {cycle_info['cycle_date']} (Cycle {cycle_info['cycle_number']})")
            logger.info(f"  Total Records: {cycle_info['total_records']}")
            logger.info(f"  Anomalies Found: {cycle_info['anomaly_count']}")
            
            if summary['anomaly_breakdown']:
                logger.info("  Anomaly Breakdown by Bill Type:")
                for bill_type, count, avg_dev, avg_pct in summary['anomaly_breakdown']:
                    logger.info(f"    {bill_type}: {count} anomalies")
        
        return cycle_id, summary
        
    except Exception as e:
        logger.error(f"Database processing failed: {e}")
        if 'cycle_id' in locals():
            db_integration.log_processing_event(cycle_id, f"Processing failed: {e}", "ERROR")
        raise
    finally:
        del db_integration

# ---------------------------
# 7. Output Results (Enhanced)
# ---------------------------
def output_results(df, mm_cc_yyyy, cycle_id=None):
    """
    Output results to Excel files (anomaly reports for analysts).
    """
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
                
    logger.info(f"Anomaly report saved to: {anomaly_file_xlsx}")
    
    # If we have a cycle_id, also export the full dataset from database
    if cycle_id:
        db_integration = DatabaseIntegration()
        try:
            db_output_path = os.path.join("data", "Database_Exports", f"Full_Cycle_Data_{mm_cc_yyyy}.xlsx")
            os.makedirs(os.path.dirname(db_output_path), exist_ok=True)
            
            if db_integration.export_cycle_to_excel(cycle_id, db_output_path):
                logger.info(f"Full cycle data exported to: {db_output_path}")
        except Exception as e:
            logger.error(f"Database export failed: {e}")
        finally:
            del db_integration

# ---------------------------
# 8. Database Query Functions
# ---------------------------
def get_processing_history():
    """Get processing history from database."""
    db_integration = DatabaseIntegration()
    try:
        cycles = db_integration.get_all_cycles()
        logger.info("Processing History:")
        for cycle in cycles:
            cycle_id, cycle_date, cycle_num, year, month, total_rec, anomaly_count, status, timestamp = cycle
            logger.info(f"  Cycle {cycle_id}: {cycle_date} - {total_rec} records, {anomaly_count} anomalies ({status})")
        return cycles
    finally:
        del db_integration

def get_code_history(billing_code):
    """Get historical data for a specific billing code."""
    db_integration = DatabaseIntegration()
    try:
        history = db_integration.get_billing_code_history(billing_code)
        logger.info(f"History for billing code {billing_code}:")
        for record in history:
            cycle_id, code, bill_type, amount, rolling_avg, deviation, is_anomaly, cycle_date, timestamp = record
            logger.info(f"  {cycle_date}: ${amount:,.2f} (deviation: ${deviation:,.2f}, anomaly: {is_anomaly})")
        return history
    finally:
        del db_integration

# ---------------------------
# 9. Main Execution
# ---------------------------
if __name__ == "__main__":
    # Accept file path as argument
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Load and process data
        df, mm_cc_yyyy, file_path = load_sample_billing_data(filepath)
        df = clean_data(df)
        df = calculate_rolling_average(df)
        df = calculate_deltas(df)
        df = flag_special_cases(df)
        df = flag_anomalies(df)
        
        # Process with database integration
        cycle_id, summary = process_with_database(df, mm_cc_yyyy, file_path)
        
        # Output results
        output_results(df, mm_cc_yyyy, cycle_id)
        
        logger.info("Anomaly detection with database integration complete.")
        
        # Show processing history
        get_processing_history()
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1) 