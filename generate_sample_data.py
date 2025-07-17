import pandas as pd
import numpy as np
import os

# Output directories
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Parameters
n_codes_per_type = 20
months = [f"{i}_Months_ago" for i in range(5, 0, -1)]
current_month = "Active Month"

# Helper to generate codes and descriptions
def make_codes(prefix, n):
    codes = [f"{prefix}{str(i).zfill(3)}" for i in range(1, n+1)]
    descs = [f"Description for {code}" for code in codes]
    return codes, descs

# 1. Generate Code Description File (for two categories)
for cat, prefix in zip(["Single Event Charges", "Account Corrections"], ["SEC", "ACR"]):
    codes, descs = make_codes(prefix, n_codes_per_type)
    df_desc = pd.DataFrame({
        "Billing_CODE": codes,
        "Billing Code Description": descs
    })
    df_desc.to_excel(os.path.join(DATA_DIR, f"{cat.replace(' ', '_')}_Descriptions.xlsx"), index=False)

# 2. Generate Billing Cycle Excel File with 4 sheets
def make_sheet(prefix, n, with_desc):
    codes, descs = make_codes(prefix, n)
    data = {
        "Year": np.random.choice([2022, 2023], n),
        "Month": np.random.choice(range(1, 13), n),
        "Bill Cycle Number": np.random.choice(range(1, 4), n),
        "Bill_TYPE": [prefix]*n,
        "Billing_CODE": codes,
    }
    for m in months:
        data[m] = np.random.gamma(100, 2, n).round(2)
    data[current_month] = np.random.gamma(100, 2, n).round(2)
    df = pd.DataFrame(data)
    if with_desc:
        df["Billing Code Description"] = descs
    return df

sheets = {
    "Single Event Charges": make_sheet("SEC", n_codes_per_type, True),
    "Account Corrections": make_sheet("ACR", n_codes_per_type, True),
    "Subscription Plans": make_sheet("SUB", n_codes_per_type, False),
    "Line Add-ons": make_sheet("ADD", n_codes_per_type, False),
}

billing_file = os.path.join(DATA_DIR, "Sample_Billing_Cycle.xlsx")
with pd.ExcelWriter(billing_file, engine="openpyxl") as writer:
    for sheet, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet, index=False)

print(f"Sample billing cycle and description files generated in '{DATA_DIR}/'") 