import pandas as pd
import numpy as np
import os
import random

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

year = 2025
bill_cycle_number = random.choice([1, 2, 3])
# Choose a single month for the entire file
chosen_month = random.randint(1, 12)

# Load available codes from description files for SEC and ACR
def get_available_codes(desc_path):
    df = pd.read_excel(desc_path)
    return list(df['Billing_CODE'])

SEC_CODES = get_available_codes(os.path.join('data', 'descriptions', 'Single_Event_Charges_Descriptions.xlsx'))
ACR_CODES = get_available_codes(os.path.join('data', 'descriptions', 'Account_Corrections_Descriptions.xlsx'))

# Helper to generate codes for SUB and ADD
def make_codes(prefix, n):
    return [f"{prefix}{str(i).zfill(3)}" for i in range(1, n+1)]

def make_sheet(prefix, n, available_codes=None):
    if available_codes is not None:
        # Randomly sample from available codes (with replacement if n > len(available_codes))
        codes = random.choices(available_codes, k=n)
    else:
        codes = make_codes(prefix, n)
    base_values = np.random.uniform(1_000_000, 17_000_000, n)
    data = {
        "Year": [year] * n,
        "Month": [chosen_month] * n,
        "Bill Cycle Number": [bill_cycle_number] * n,
        "Bill_TYPE": [prefix] * n,
        "Billing_CODE": codes,
    }
    for i, m in enumerate(months[::-1]):
        data[m] = (base_values + i * np.random.uniform(100_000, 500_000, n) + np.random.normal(0, 200_000, n)).clip(0, 18_000_000).round(2)
    data[current_month] = (base_values + 5 * np.random.uniform(100_000, 500_000, n) + np.random.normal(0, 1_000_000, n)).clip(0, 18_000_000).round(2)
    data["Billing Code Description"] = ["" for _ in range(n)]
    df = pd.DataFrame(data)
    return df

sheets = {}
for sheet_name, prefix in sheet_types:
    n_rows = random.randint(100, 200)
    if prefix == "SEC":
        sheets[sheet_name] = make_sheet(prefix, n_rows, available_codes=SEC_CODES)
    elif prefix == "ACR":
        sheets[sheet_name] = make_sheet(prefix, n_rows, available_codes=ACR_CODES)
    else:
        sheets[sheet_name] = make_sheet(prefix, n_rows)

month_str = str(chosen_month).zfill(2)
billing_file = os.path.join(SAMPLE_DATA_DIR, f"Sample_Billing_Cycle_{month_str}-{bill_cycle_number}-{year}.xlsx")
with pd.ExcelWriter(billing_file, engine="openpyxl") as writer:
    for sheet, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet, index=False)

print(f"Sample billing cycle file generated in '{billing_file}'") 