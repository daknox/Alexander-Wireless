"""
Simple Database Viewer for Telecom Billing Anomaly Detection
Author: Dylan Alexander Knox
Description: View database contents without external tools
"""

import sqlite3
import pandas as pd
import os

def view_database_summary():
    """Show a summary of what's in the database."""
    if not os.path.exists('billing_anomaly_detection.db'):
        print("❌ Database file not found!")
        return
    
    print("=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)
    
    conn = sqlite3.connect('billing_anomaly_detection.db')
    
    # Get all table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📊 Database contains {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Show processing cycles
    print(f"\n🔄 PROCESSING CYCLES:")
    cycles_df = pd.read_sql_query("""
        SELECT cycle_id, cycle_date, cycle_number, year, month, 
               total_records, anomaly_count, status, created_at
        FROM processing_cycles 
        ORDER BY created_at DESC
        LIMIT 10
    """, conn)
    
    if not cycles_df.empty:
        print(f"Found {len(cycles_df)} processing cycles:")
        for _, row in cycles_df.iterrows():
            print(f"  Cycle {row['cycle_number']} ({row['month']}/{row['year']}): "
                  f"{row['total_records']} records, {row['anomaly_count']} anomalies")
    else:
        print("  No processing cycles found")
    
    # Show billing data summary
    print(f"\n💰 BILLING DATA:")
    billing_df = pd.read_sql_query("""
        SELECT COUNT(*) as total_records,
               COUNT(DISTINCT billing_code) as unique_codes,
               COUNT(DISTINCT audit_type) as audit_types
        FROM billing_data
    """, conn)
    
    if not billing_df.empty and billing_df.iloc[0]['total_records'] > 0:
        print(f"  Total billing records: {billing_df.iloc[0]['total_records']}")
        print(f"  Unique billing codes: {billing_df.iloc[0]['unique_codes']}")
        print(f"  Audit types: {billing_df.iloc[0]['audit_types']}")
    else:
        print("  No billing data found")
    
    # Show recent anomalies
    print(f"\n🚨 RECENT ANOMALIES:")
    anomalies_df = pd.read_sql_query("""
        SELECT billing_code, audit_type, active_month, rolling_avg, 
               active_vs_avg, pct_change_active_vs_avg, is_anomaly
        FROM billing_data 
        WHERE is_anomaly = 1
        ORDER BY cycle_id DESC
        LIMIT 10
    """, conn)
    
    if not anomalies_df.empty:
        print(f"Found {len(anomalies_df)} recent anomalies:")
        for _, row in anomalies_df.iterrows():
            print(f"  {row['billing_code']} ({row['audit_type']}): "
                  f"${row['active_month']:,.0f} vs avg ${row['rolling_avg']:,.0f} "
                  f"({row['pct_change_active_vs_avg']:.1%} change)")
    else:
        print("  No anomalies found")
    
    conn.close()
    print("\n" + "=" * 60)

def export_sample_data():
    """Export sample data to CSV for easy viewing."""
    if not os.path.exists('billing_anomaly_detection.db'):
        print("❌ Database file not found!")
        return
    
    print("\n📤 EXPORTING SAMPLE DATA TO CSV...")
    
    conn = sqlite3.connect('billing_anomaly_detection.db')
    
    # Export recent billing data
    billing_df = pd.read_sql_query("""
        SELECT * FROM billing_data 
        ORDER BY cycle_id DESC 
        LIMIT 100
    """, conn)
    
    if not billing_df.empty:
        billing_df.to_csv('sample_billing_data.csv', index=False)
        print(f"✅ Exported {len(billing_df)} billing records to 'sample_billing_data.csv'")
    
    # Export processing cycles
    cycles_df = pd.read_sql_query("""
        SELECT * FROM processing_cycles 
        ORDER BY created_at DESC
    """, conn)
    
    if not cycles_df.empty:
        cycles_df.to_csv('processing_cycles.csv', index=False)
        print(f"✅ Exported {len(cycles_df)} processing cycles to 'processing_cycles.csv'")
    
    conn.close()
    print("\n💡 You can now open these CSV files in any text editor or spreadsheet app!")

def main():
    """Main function to view database contents."""
    print("🔍 Telecom Billing Database Viewer")
    print("=" * 60)
    
    view_database_summary()
    export_sample_data()
    
    print("\n📋 NEXT STEPS:")
    print("1. Open 'sample_billing_data.csv' in any text editor or spreadsheet app")
    print("2. Upload Excel files from 'data/Anomalies/' to Google Sheets")
    print("3. Download DB Browser for SQLite for advanced database viewing")
    print("4. Use LibreOffice Calc as free Excel alternative")

if __name__ == "__main__":
    main() 