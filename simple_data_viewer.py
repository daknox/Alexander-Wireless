#!/usr/bin/env python3
"""
Simple Command-Line Data Viewer for Dummy Data Generation Output
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subheader(title):
    """Print a formatted subheader"""
    print(f"\n--- {title} ---")

def view_data_overview():
    """Display overview of available data files"""
    print_header("DATA OVERVIEW")
    
    DATA_DIR = "data"
    if not os.path.exists(DATA_DIR):
        print(f"❌ Data directory '{DATA_DIR}' not found.")
        print("Please run 'python generate_sample_data.py' first.")
        return False
    
    print(f"📁 Data directory: {DATA_DIR}")
    
    # Check billing cycle file
    billing_file = os.path.join(DATA_DIR, "Sample_Billing_Cycle.xlsx")
    if os.path.exists(billing_file):
        print(f"✅ Sample_Billing_Cycle.xlsx found")
        try:
            excel_file = pd.ExcelFile(billing_file)
            print(f"   Sheets: {', '.join(excel_file.sheet_names)}")
            for sheet in excel_file.sheet_names:
                df = pd.read_excel(billing_file, sheet_name=sheet)
                print(f"   - {sheet}: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    else:
        print("❌ Sample_Billing_Cycle.xlsx not found")
    
    # Check description files
    desc_files = [
        "Single_Event_Charges_Descriptions.xlsx",
        "Account_Corrections_Descriptions.xlsx"
    ]
    
    print("\n📝 Description files:")
    for desc_file in desc_files:
        file_path = os.path.join(DATA_DIR, desc_file)
        if os.path.exists(file_path):
            print(f"   ✅ {desc_file}")
        else:
            print(f"   ⚠️  {desc_file} not found")
    
    return True

def view_billing_data():
    """Display billing cycle data"""
    print_header("BILLING CYCLE DATA")
    
    billing_file = os.path.join("data", "Sample_Billing_Cycle.xlsx")
    if not os.path.exists(billing_file):
        print("❌ Billing cycle file not found.")
        return
    
    try:
        excel_file = pd.ExcelFile(billing_file)
        sheet_names = excel_file.sheet_names
        
        print(f"Available sheets: {', '.join(sheet_names)}")
        
        for sheet_name in sheet_names:
            print_subheader(f"SHEET: {sheet_name}")
            df = pd.read_excel(billing_file, sheet_name=sheet_name)
            
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Show first few rows
            print("\nFirst 5 rows:")
            print(df.head().to_string(index=False))
            
            # Show basic stats for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                print(f"\nNumeric columns statistics:")
                print(df[numeric_cols].describe().round(2))
            
            print("\n" + "-"*40)
            
    except Exception as e:
        print(f"❌ Error reading billing data: {e}")

def view_code_descriptions():
    """Display code descriptions"""
    print_header("CODE DESCRIPTIONS")
    
    desc_files = [
        ("Single Event Charges", "Single_Event_Charges_Descriptions.xlsx"),
        ("Account Corrections", "Account_Corrections_Descriptions.xlsx")
    ]
    
    for title, filename in desc_files:
        file_path = os.path.join("data", filename)
        if os.path.exists(file_path):
            print_subheader(title)
            df = pd.read_excel(file_path)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nData:")
            print(df.to_string(index=False))
            print("\n" + "-"*40)
        else:
            print(f"⚠️  {filename} not found")

def view_analytics():
    """Display basic analytics"""
    print_header("ANALYTICS")
    
    billing_file = os.path.join("data", "Sample_Billing_Cycle.xlsx")
    if not os.path.exists(billing_file):
        print("❌ Billing cycle file not found.")
        return
    
    try:
        excel_file = pd.ExcelFile(billing_file)
        
        # Combine all sheets for analysis
        all_data = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(billing_file, sheet_name=sheet_name)
            df['Sheet_Name'] = sheet_name
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        print(f"Total records: {len(combined_df)}")
        print(f"Total sheets: {len(excel_file.sheet_names)}")
        
        # Data distribution by sheet
        print_subheader("Records by Sheet")
        sheet_counts = combined_df['Sheet_Name'].value_counts()
        for sheet, count in sheet_counts.items():
            print(f"  {sheet}: {count} records")
        
        # Monthly distribution
        if 'Month' in combined_df.columns:
            print_subheader("Records by Month")
            month_counts = combined_df['Month'].value_counts().sort_index()
            for month, count in month_counts.items():
                print(f"  Month {month}: {count} records")
        
        # Year distribution
        if 'Year' in combined_df.columns:
            print_subheader("Records by Year")
            year_counts = combined_df['Year'].value_counts().sort_index()
            for year, count in year_counts.items():
                print(f"  {year}: {count} records")
        
        # Bill cycle distribution
        if 'Bill Cycle Number' in combined_df.columns:
            print_subheader("Records by Bill Cycle")
            cycle_counts = combined_df['Bill Cycle Number'].value_counts().sort_index()
            for cycle, count in cycle_counts.items():
                print(f"  Cycle {cycle}: {count} records")
        
        # Monthly data trends
        month_columns = [col for col in combined_df.columns if 'Months_ago' in col or col == 'Active Month']
        if month_columns:
            print_subheader("Monthly Data Averages")
            for col in month_columns:
                avg_val = combined_df[col].mean()
                print(f"  {col}: {avg_val:.2f}")
        
    except Exception as e:
        print(f"❌ Error in analytics: {e}")

def main():
    """Main function"""
    print_header("DUMMY DATA VIEWER")
    print("Simple command-line viewer for dummy data generation output")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "overview":
            view_data_overview()
        elif command == "billing":
            view_billing_data()
        elif command == "descriptions":
            view_code_descriptions()
        elif command == "analytics":
            view_analytics()
        elif command == "all":
            view_data_overview()
            view_billing_data()
            view_code_descriptions()
            view_analytics()
        else:
            print("❌ Unknown command. Available commands:")
            print("  overview     - Show data overview")
            print("  billing      - Show billing cycle data")
            print("  descriptions - Show code descriptions")
            print("  analytics    - Show analytics")
            print("  all          - Show everything")
    else:
        # Interactive mode
        while True:
            print("\n" + "="*40)
            print("DUMMY DATA VIEWER MENU")
            print("="*40)
            print("1. Data Overview")
            print("2. Billing Cycle Data")
            print("3. Code Descriptions")
            print("4. Analytics")
            print("5. Show Everything")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                view_data_overview()
            elif choice == "2":
                view_billing_data()
            elif choice == "3":
                view_code_descriptions()
            elif choice == "4":
                view_analytics()
            elif choice == "5":
                view_data_overview()
                view_billing_data()
                view_code_descriptions()
                view_analytics()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()