"""
Enhanced Sample Data Generator for Telecom Billing Anomaly Detection
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: Generates 30 billing cycles across 3 sequential months for comprehensive testing.
"""

import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

# Output directory
DATA_DIR = "data"
SAMPLE_DATA_DIR = os.path.join(DATA_DIR, "sample_data")
if not os.path.exists(SAMPLE_DATA_DIR):
    os.makedirs(SAMPLE_DATA_DIR)

months = [f"{i}_Months_ago" for i in range(5, 0, -1)]
current_month = "Active Month"
sheet_types = [
    ("Single Event Charges", "SEC"),
    ("Account Corrections", "ACR"),
    ("Subscription Plans", "SUB"),
    ("Line Add-ons", "ADD"),
]

# Configuration for extended data generation
START_MONTH = 1  # January
START_YEAR = 2025
CYCLES_PER_MONTH = 10
TOTAL_MONTHS = 3
TOTAL_CYCLES = CYCLES_PER_MONTH * TOTAL_MONTHS

# Load available codes from description files for SEC and ACR
def get_available_codes(desc_path):
    df = pd.read_excel(desc_path)
    return list(df['Billing_CODE'])

SEC_CODES = get_available_codes(os.path.join('data', 'descriptions', 'Single_Event_Charges_Descriptions.xlsx'))
ACR_CODES = get_available_codes(os.path.join('data', 'descriptions', 'Account_Corrections_Descriptions.xlsx'))

# Helper to generate codes for SUB and ADD
def make_codes(prefix, n):
    return [f"{prefix}{str(i).zfill(3)}" for i in range(1, n+1)]

def make_sheet(prefix, n, available_codes=None, month_offset=0):
    """Generate sheet data with month offset for historical data."""
    if available_codes is not None:
        # Randomly sample from available codes (with replacement if n > len(available_codes))
        codes = random.choices(available_codes, k=n)
    else:
        codes = make_codes(prefix, n)
    
    # Base values with some variation based on month
    base_values = np.random.uniform(1_000_000, 17_000_000, n) + (month_offset * 100_000)
    
    data = {
        "Year": [START_YEAR] * n,
        "Month": [START_MONTH + month_offset] * n,
        "Bill Cycle Number": [1] * n,  # Will be updated per cycle
        "Bill_TYPE": [prefix] * n,
        "Billing_CODE": codes,
    }
    
    # Generate historical data with increasing trend over months
    for i, m in enumerate(months[::-1]):
        month_trend = month_offset + (5 - i)  # Historical months
        data[m] = (base_values + 
                   month_trend * np.random.uniform(50_000, 300_000, n) + 
                   np.random.normal(0, 200_000, n)).clip(0, 18_000_000).round(2)
    
    # Current month (active month)
    current_month_trend = month_offset + 5
    data[current_month] = (base_values + 
                          current_month_trend * np.random.uniform(100_000, 500_000, n) + 
                          np.random.normal(0, 1_000_000, n)).clip(0, 18_000_000).round(2)
    
    data["Billing Code Description"] = ["" for _ in range(n)]
    df = pd.DataFrame(data)
    return df

def generate_cycle_data(month, year, cycle_number, month_offset=0):
    """Generate data for a specific cycle."""
    sheets = {}
    
    for sheet_name, prefix in sheet_types:
        n_rows = random.randint(100, 200)
        if prefix == "SEC":
            sheets[sheet_name] = make_sheet(prefix, n_rows, available_codes=SEC_CODES, month_offset=month_offset)
        elif prefix == "ACR":
            sheets[sheet_name] = make_sheet(prefix, n_rows, available_codes=ACR_CODES, month_offset=month_offset)
        else:
            sheets[sheet_name] = make_sheet(prefix, n_rows, month_offset=month_offset)
        
        # Update cycle number for all sheets
        sheets[sheet_name]["Bill Cycle Number"] = cycle_number
        sheets[sheet_name]["Year"] = year
        sheets[sheet_name]["Month"] = month
    
    return sheets

def generate_extended_sample_data():
    """Generate 30 cycles across 3 months with random cycle numbers 1-30 in sequential order."""
    generated_files = []
    
    # Create random cycle numbers 1-30 for each month
    all_cycle_numbers = list(range(1, 31))  # 1-30
    
    for month_offset in range(TOTAL_MONTHS):
        current_month = START_MONTH + month_offset
        current_year = START_YEAR
        
        # Get 10 random cycle numbers for this month (in sequential order)
        month_cycle_numbers = sorted(random.sample(all_cycle_numbers, CYCLES_PER_MONTH))
        
        for i, cycle_num in enumerate(month_cycle_numbers):
            # Generate data for this cycle
            sheets = generate_cycle_data(current_month, current_year, cycle_num, month_offset)
            
            # Create filename
            month_str = str(current_month).zfill(2)
            billing_file = os.path.join(SAMPLE_DATA_DIR, 
                                      f"Sample_Billing_Cycle_{month_str}-{cycle_num}-{current_year}.xlsx")
            
            # Write to Excel
            with pd.ExcelWriter(billing_file, engine="openpyxl") as writer:
                for sheet, df in sheets.items():
                    df.to_excel(writer, sheet_name=sheet, index=False)
            
            generated_files.append(billing_file)
            print(f"Generated cycle {cycle_num} for month {current_month}/{current_year}: {billing_file}")
    
    return generated_files

def get_next_processing_month():
    """Get the next month to process after the demo data."""
    # After 3 months of demo data, process month 4
    next_month = START_MONTH + TOTAL_MONTHS
    next_year = START_YEAR
    
    # If we go past December, adjust year and month
    if next_month > 12:
        next_month = next_month - 12
        next_year = START_YEAR + 1
    
    return next_month, next_year

if __name__ == "__main__":
    print("Generating extended sample data...")
    print(f"Configuration:")
    print(f"  - Start Month: {START_MONTH}/{START_YEAR}")
    print(f"  - Cycles per month: {CYCLES_PER_MONTH}")
    print(f"  - Total months: {TOTAL_MONTHS}")
    print(f"  - Total cycles: {TOTAL_CYCLES}")
    
    generated_files = generate_extended_sample_data()
    
    print(f"\nGenerated {len(generated_files)} billing cycle files:")
    for file in generated_files:
        print(f"  {file}")
    
    next_month, next_year = get_next_processing_month()
    print(f"\nNext processing month: {next_month}/{next_year}")
    print("Sample data generation complete!") 