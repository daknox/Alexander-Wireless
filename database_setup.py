"""
SQLite Database Setup for Telecom Billing Anomaly Detection
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: Creates and initializes the SQLite database for storing all billing data and anomaly detection results.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BillingDatabase:
    def __init__(self, db_path="billing_anomaly_detection.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def create_tables(self):
        """Create all necessary tables for the billing anomaly detection system."""
        
        # 1. Processing Cycles Table - Track each billing cycle processed
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_cycles (
                cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_date TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                file_path TEXT,
                processing_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_records INTEGER,
                anomaly_count INTEGER,
                status TEXT DEFAULT 'completed',
                notes TEXT
            )
        """)
        
        # 2. Billing Codes Master Table - Store all unique billing codes
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_codes (
                code_id INTEGER PRIMARY KEY AUTOINCREMENT,
                billing_code TEXT UNIQUE NOT NULL,
                bill_type TEXT NOT NULL,
                description TEXT,
                first_seen_date TEXT,
                last_seen_date TEXT,
                total_occurrences INTEGER DEFAULT 0,
                anomaly_count INTEGER DEFAULT 0
            )
        """)
        
        # 3. Billing Data Table - Store all processed billing records
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_data (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                code_id INTEGER NOT NULL,
                billing_code TEXT NOT NULL,
                bill_type TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                bill_cycle_number INTEGER NOT NULL,
                amount_5_months_ago REAL,
                amount_4_months_ago REAL,
                amount_3_months_ago REAL,
                amount_2_months_ago REAL,
                amount_1_month_ago REAL,
                active_month_amount REAL NOT NULL,
                rolling_average REAL,
                active_vs_avg REAL,
                pct_change_active_vs_avg REAL,
                mom_change REAL,
                pct_change_mom REAL,
                drop_to_zero BOOLEAN DEFAULT FALSE,
                new_code BOOLEAN DEFAULT FALSE,
                active_vs_avg_z_score REAL,
                is_anomaly BOOLEAN DEFAULT FALSE,
                anomaly_reason TEXT,
                description TEXT,
                processing_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cycle_id) REFERENCES processing_cycles (cycle_id),
                FOREIGN KEY (code_id) REFERENCES billing_codes (code_id)
            )
        """)
        
        # 4. Processing Log Table - Track processing events
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER,
                log_level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cycle_id) REFERENCES processing_cycles (cycle_id)
            )
        """)
        
        # 5. Configuration Table - Store processing parameters
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_config (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_data_cycle_id ON billing_data(cycle_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_data_code_id ON billing_data(code_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_data_anomaly ON billing_data(is_anomaly)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_billing_codes_code ON billing_codes(billing_code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_log_cycle_id ON processing_log(cycle_id)")
        
        self.conn.commit()
        logger.info("All tables created successfully")
        
    def insert_default_config(self):
        """Insert default processing configuration."""
        default_configs = [
            ("z_score_threshold", "2.5", "Z-score threshold for anomaly detection"),
            ("percent_change_threshold", "0.5", "Percent change threshold (50%)"),
            ("sec_absolute_threshold", "50000", "Single Event Charges absolute change threshold"),
            ("acr_absolute_threshold", "25000", "Account Corrections absolute change threshold"),
            ("sub_absolute_threshold", "50000", "Subscription Plans absolute change threshold"),
            ("add_absolute_threshold", "25000", "Line Add-ons absolute change threshold"),
            ("sec_percent_threshold", "0.25", "Single Event Charges percent change threshold"),
            ("acr_percent_threshold", "0.25", "Account Corrections percent change threshold"),
            ("sub_percent_threshold", "0.25", "Subscription Plans percent change threshold"),
            ("add_percent_threshold", "0.25", "Line Add-ons percent change threshold")
        ]
        
        for config_name, config_value, description in default_configs:
            self.cursor.execute("""
                INSERT OR REPLACE INTO processing_config (config_name, config_value, description)
                VALUES (?, ?, ?)
            """, (config_name, config_value, description))
            
        self.conn.commit()
        logger.info("Default configuration inserted")
        
    def get_config_value(self, config_name):
        """Get a configuration value from the database."""
        self.cursor.execute("SELECT config_value FROM processing_config WHERE config_name = ?", (config_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None
        
    def log_processing_event(self, cycle_id, log_level, message):
        """Log a processing event."""
        self.cursor.execute("""
            INSERT INTO processing_log (cycle_id, log_level, message)
            VALUES (?, ?, ?)
        """, (cycle_id, log_level, message))
        self.conn.commit()
        
    def get_processing_stats(self, cycle_id):
        """Get processing statistics for a cycle."""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomaly_count,
                COUNT(DISTINCT billing_code) as unique_codes,
                COUNT(DISTINCT bill_type) as bill_types
            FROM billing_data 
            WHERE cycle_id = ?
        """, (cycle_id,))
        return self.cursor.fetchone()
        
    def get_anomaly_summary(self, cycle_id):
        """Get anomaly summary for a cycle."""
        self.cursor.execute("""
            SELECT 
                bill_type,
                COUNT(*) as anomaly_count,
                AVG(active_vs_avg) as avg_deviation,
                AVG(pct_change_active_vs_avg) as avg_percent_change
            FROM billing_data 
            WHERE cycle_id = ? AND is_anomaly = 1
            GROUP BY bill_type
        """, (cycle_id,))
        return self.cursor.fetchall()
        
    def export_cycle_data(self, cycle_id, output_path):
        """Export all data for a specific cycle to Excel."""
        # Get cycle info
        self.cursor.execute("SELECT * FROM processing_cycles WHERE cycle_id = ?", (cycle_id,))
        cycle_info = self.cursor.fetchone()
        
        if not cycle_info:
            logger.error(f"Cycle {cycle_id} not found")
            return False
            
        # Get all billing data for the cycle
        query = """
            SELECT 
                bd.*,
                bc.description as code_description
            FROM billing_data bd
            LEFT JOIN billing_codes bc ON bd.code_id = bc.code_id
            WHERE bd.cycle_id = ?
            ORDER BY bd.bill_type, bd.billing_code
        """
        
        df = pd.read_sql_query(query, self.conn, params=(cycle_id,))
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All_Data', index=False)
            
            # Create anomaly summary sheet
            anomaly_df = df[df['is_anomaly'] == 1].copy()
            if not anomaly_df.empty:
                anomaly_df.to_excel(writer, sheet_name='Anomalies', index=False)
                
        logger.info(f"Cycle data exported to: {output_path}")
        return True

def setup_database():
    """Main function to set up the database."""
    db = BillingDatabase()
    
    try:
        db.connect()
        db.create_tables()
        db.insert_default_config()
        logger.info("Database setup completed successfully")
        
        # Print database info
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = db.cursor.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        db.disconnect()

if __name__ == "__main__":
    setup_database() 