"""
Database Integration for Telecom Billing Anomaly Detection
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: Handles storing all billing data and anomaly results in the SQLite database.
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from database_setup import BillingDatabase

logger = logging.getLogger(__name__)

class DatabaseIntegration:
    def __init__(self, db_path="billing_anomaly_detection.db"):
        """Initialize database integration."""
        self.db = BillingDatabase(db_path)
        self.db.connect()
        
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.disconnect()
            
    def create_processing_cycle(self, cycle_date, cycle_number, year, month, file_path=None):
        """Create a new processing cycle record."""
        self.db.cursor.execute("""
            INSERT INTO processing_cycles 
            (cycle_date, cycle_number, year, month, file_path, processing_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cycle_date, cycle_number, year, month, file_path, datetime.now()))
        
        cycle_id = self.db.cursor.lastrowid
        self.db.conn.commit()
        logger.info(f"Created processing cycle {cycle_id} for {cycle_date}")
        return cycle_id
        
    def get_or_create_billing_code(self, billing_code, bill_type, description=None):
        """Get existing billing code or create new one."""
        # Check if code exists
        self.db.cursor.execute("""
            SELECT code_id, description FROM billing_codes 
            WHERE billing_code = ? AND bill_type = ?
        """, (billing_code, bill_type))
        
        result = self.db.cursor.fetchone()
        
        if result:
            code_id, existing_description = result
            # Update description if provided and different
            if description and description != existing_description:
                self.db.cursor.execute("""
                    UPDATE billing_codes SET description = ? WHERE code_id = ?
                """, (description, code_id))
                self.db.conn.commit()
            return code_id
        else:
            # Create new billing code
            self.db.cursor.execute("""
                INSERT INTO billing_codes (billing_code, bill_type, description, first_seen_date)
                VALUES (?, ?, ?, ?)
            """, (billing_code, bill_type, description, datetime.now().strftime('%Y-%m-%d')))
            
            code_id = self.db.cursor.lastrowid
            self.db.conn.commit()
            logger.info(f"Created new billing code: {billing_code} ({bill_type})")
            return code_id
            
    def store_billing_data(self, cycle_id, df):
        """Store all billing data for a cycle."""
        records_inserted = 0
        
        for _, row in df.iterrows():
            # Get or create billing code
            code_id = self.get_or_create_billing_code(
                row['Billing_CODE'], 
                row['Bill_TYPE'],
                row.get('Billing Code Description', '')
            )
            
            # Prepare data for insertion
            data = {
                'cycle_id': cycle_id,
                'code_id': code_id,
                'billing_code': row['Billing_CODE'],
                'bill_type': row['Bill_TYPE'],
                'year': row['Year'],
                'month': row['Month'],
                'bill_cycle_number': row['Bill Cycle Number'],
                'amount_5_months_ago': row.get('5_Months_ago'),
                'amount_4_months_ago': row.get('4_Months_ago'),
                'amount_3_months_ago': row.get('3_Months_ago'),
                'amount_2_months_ago': row.get('2_Months_ago'),
                'amount_1_month_ago': row.get('1_Months_ago'),
                'active_month_amount': row['Active Month'],
                'rolling_average': row.get('Rolling_Avg'),
                'active_vs_avg': row.get('Active_vs_Avg'),
                'pct_change_active_vs_avg': row.get('Pct_Change_Active_vs_Avg'),
                'mom_change': row.get('MoM_Change'),
                'pct_change_mom': row.get('Pct_Change_MoM'),
                'drop_to_zero': row.get('Drop_to_0', False),
                'new_code': row.get('New_Code', False),
                'active_vs_avg_z_score': row.get('Active_vs_Avg_z'),
                'is_anomaly': row.get('Anomaly', False),
                'description': row.get('Billing Code Description', '')
            }
            
            # Insert billing data
            self.db.cursor.execute("""
                INSERT INTO billing_data (
                    cycle_id, code_id, billing_code, bill_type, year, month, bill_cycle_number,
                    amount_5_months_ago, amount_4_months_ago, amount_3_months_ago, 
                    amount_2_months_ago, amount_1_month_ago, active_month_amount,
                    rolling_average, active_vs_avg, pct_change_active_vs_avg,
                    mom_change, pct_change_mom, drop_to_zero, new_code,
                    active_vs_avg_z_score, is_anomaly, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['cycle_id'], data['code_id'], data['billing_code'], data['bill_type'],
                data['year'], data['month'], data['bill_cycle_number'],
                data['amount_5_months_ago'], data['amount_4_months_ago'], data['amount_3_months_ago'],
                data['amount_2_months_ago'], data['amount_1_month_ago'], data['active_month_amount'],
                data['rolling_average'], data['active_vs_avg'], data['pct_change_active_vs_avg'],
                data['mom_change'], data['pct_change_mom'], data['drop_to_zero'], data['new_code'],
                data['active_vs_avg_z_score'], data['is_anomaly'], data['description']
            ))
            
            records_inserted += 1
            
        self.db.conn.commit()
        logger.info(f"Stored {records_inserted} billing records for cycle {cycle_id}")
        return records_inserted
        
    def update_processing_cycle_stats(self, cycle_id):
        """Update processing cycle with final statistics."""
        stats = self.db.get_processing_stats(cycle_id)
        if stats:
            total_records, anomaly_count, unique_codes, bill_types = stats
            
            self.db.cursor.execute("""
                UPDATE processing_cycles 
                SET total_records = ?, anomaly_count = ?
                WHERE cycle_id = ?
            """, (total_records, anomaly_count, cycle_id))
            
            self.db.conn.commit()
            logger.info(f"Updated cycle {cycle_id} stats: {total_records} records, {anomaly_count} anomalies")
            
    def log_processing_event(self, cycle_id, message, level="INFO"):
        """Log a processing event."""
        self.db.log_processing_event(cycle_id, level, message)
        
    def get_cycle_summary(self, cycle_id):
        """Get a summary of processing results for a cycle."""
        # Get cycle info
        self.db.cursor.execute("""
            SELECT cycle_date, cycle_number, year, month, total_records, anomaly_count, status
            FROM processing_cycles WHERE cycle_id = ?
        """, (cycle_id,))
        cycle_info = self.db.cursor.fetchone()
        
        if not cycle_info:
            return None
            
        # Get anomaly breakdown by bill type
        anomaly_summary = self.db.get_anomaly_summary(cycle_id)
        
        return {
            'cycle_info': {
                'cycle_id': cycle_id,
                'cycle_date': cycle_info[0],
                'cycle_number': cycle_info[1],
                'year': cycle_info[2],
                'month': cycle_info[3],
                'total_records': cycle_info[4],
                'anomaly_count': cycle_info[5],
                'status': cycle_info[6]
            },
            'anomaly_breakdown': anomaly_summary
        }
        
    def export_cycle_to_excel(self, cycle_id, output_path):
        """Export cycle data to Excel file."""
        return self.db.export_cycle_data(cycle_id, output_path)
        
    def get_all_cycles(self):
        """Get list of all processed cycles."""
        self.db.cursor.execute("""
            SELECT cycle_id, cycle_date, cycle_number, year, month, 
                   total_records, anomaly_count, status, processing_timestamp
            FROM processing_cycles 
            ORDER BY processing_timestamp DESC
        """)
        return self.db.cursor.fetchall()
        
    def get_billing_code_history(self, billing_code):
        """Get historical data for a specific billing code."""
        self.db.cursor.execute("""
            SELECT bd.cycle_id, bd.billing_code, bd.bill_type, bd.active_month_amount,
                   bd.rolling_average, bd.active_vs_avg, bd.is_anomaly,
                   pc.cycle_date, pc.processing_timestamp
            FROM billing_data bd
            JOIN processing_cycles pc ON bd.cycle_id = pc.cycle_id
            WHERE bd.billing_code = ?
            ORDER BY pc.processing_timestamp DESC
        """, (billing_code,))
        return self.db.cursor.fetchall() 