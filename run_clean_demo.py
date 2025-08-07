"""
Clean Demo Script for Telecom Billing Anomaly Detection
Author: Dylan Alexander Knox
Date: 7/14/2025
Description: Streamlined demo with 30 cycles generated, stored in SQLite, anomaly detection on 2 cycles.
"""

import os
import sys
import logging
import random
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['pandas', 'numpy', 'openpyxl', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Please install missing packages using: python -m pip install -r requirements.txt")
        return False
    
    logger.info("All required dependencies are installed.")
    return True

def setup_database():
    """Set up the SQLite database."""
    logger.info("Setting up SQLite database...")
    try:
        from database_setup import setup_database
        setup_database()
        logger.info("Database setup completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def generate_and_store_30_cycles():
    """Generate 30 cycles and store them all in SQLite."""
    logger.info("Generating and storing 30 cycles in SQLite...")
    try:
        import generate_extended_sample_data
        from database_integration import DatabaseIntegration
        
        # Generate 30 cycles across 3 months
        generated_files = generate_extended_sample_data.generate_extended_sample_data()
        logger.info(f"Generated {len(generated_files)} billing cycle files")
        
        # Store all cycles in database
        db_integration = DatabaseIntegration()
        
        stored_count = 0
        for file_path in generated_files:
            try:
                # Extract cycle info from filename
                import re
                match = re.search(r"Sample_Billing_Cycle_(\d{2})-(\d+)-(\d{4})", os.path.basename(file_path))
                if match:
                    month = int(match.group(1))
                    cycle_num = int(match.group(2))
                    year = int(match.group(3))
                    cycle_date = f"{year}-{month:02d}-01"
                    
                    # Create processing cycle
                    cycle_id = db_integration.create_processing_cycle(
                        cycle_date=cycle_date,
                        cycle_number=cycle_num,
                        year=year,
                        month=month,
                        file_path=file_path
                    )
                    
                    # Load data and store in database
                    import anomaly_detection_with_db
                    df, mm_cc_yyyy, _ = anomaly_detection_with_db.load_sample_billing_data(file_path)
                    df = anomaly_detection_with_db.clean_data(df)
                    df = anomaly_detection_with_db.calculate_rolling_average(df)
                    df = anomaly_detection_with_db.calculate_deltas(df)
                    df = anomaly_detection_with_db.flag_special_cases(df)
                    df = anomaly_detection_with_db.flag_anomalies(df)
                    
                    # Store in database
                    records_stored = db_integration.store_billing_data(cycle_id, df)
                    db_integration.update_processing_cycle_stats(cycle_id)
                    
                    stored_count += 1
                    logger.info(f"Stored cycle {cycle_num} for month {month}/{year} ({records_stored} records)")
                    
            except Exception as e:
                logger.error(f"Failed to store cycle from {file_path}: {e}")
                continue
        
        del db_integration
        logger.info(f"Successfully stored {stored_count} cycles in database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate and store cycles: {e}")
        return False

def run_anomaly_detection_demo(num_cycles=2):
    """Run anomaly detection demo on a few cycles."""
    logger.info(f"Running anomaly detection demo on {num_cycles} cycles...")
    try:
        import anomaly_detection_with_db
        from database_integration import DatabaseIntegration
        
        # Get recent cycles from database
        db_integration = DatabaseIntegration()
        cycles = db_integration.get_all_cycles()
        
        if len(cycles) < num_cycles:
            logger.error(f"Not enough cycles in database. Found {len(cycles)}, need {num_cycles}")
            return False
        
        # Select random cycles for demo
        demo_cycles = random.sample(cycles, num_cycles)
        
        for i, cycle in enumerate(demo_cycles):
            cycle_id, cycle_date, cycle_num, year, month, total_rec, anomaly_count, status, timestamp = cycle
            
            logger.info(f"Running anomaly detection demo {i+1}/{num_cycles}: Cycle {cycle_num} ({month}/{year})")
            
            # Get the file path for this cycle
            db_integration.db.cursor.execute("""
                SELECT file_path FROM processing_cycles WHERE cycle_id = ?
            """, (cycle_id,))
            result = db_integration.db.cursor.fetchone()
            
            if result and result[0]:
                file_path = result[0]
                
                # Run anomaly detection and generate Excel report
                df, mm_cc_yyyy, _ = anomaly_detection_with_db.load_sample_billing_data(file_path)
                df = anomaly_detection_with_db.clean_data(df)
                df = anomaly_detection_with_db.calculate_rolling_average(df)
                df = anomaly_detection_with_db.calculate_deltas(df)
                df = anomaly_detection_with_db.flag_special_cases(df)
                df = anomaly_detection_with_db.flag_anomalies(df)
                
                # Generate Excel report (for analyst review)
                anomaly_detection_with_db.output_results(df, mm_cc_yyyy, cycle_id)
                
                logger.info(f"Generated anomaly report for cycle {cycle_num}")
            else:
                logger.warning(f"No file path found for cycle {cycle_id}")
        
        del db_integration
        logger.info("Anomaly detection demo completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Anomaly detection demo failed: {e}")
        return False

def show_database_summary():
    """Show a summary of the database contents."""
    logger.info("Database Summary:")
    try:
        from database_integration import DatabaseIntegration
        
        db = DatabaseIntegration()
        
        # Get all cycles
        cycles = db.get_all_cycles()
        if cycles:
            logger.info(f"Total cycles in database: {len(cycles)}")
            
            # Group by month
            monthly_stats = {}
            for cycle in cycles:
                cycle_id, cycle_date, cycle_num, year, month, total_rec, anomaly_count, status, timestamp = cycle
                month_key = f"{year}-{month:02d}"
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {"cycles": 0, "total_records": 0, "total_anomalies": 0}
                monthly_stats[month_key]["cycles"] += 1
                monthly_stats[month_key]["total_records"] += total_rec or 0
                monthly_stats[month_key]["total_anomalies"] += anomaly_count or 0
            
            logger.info("Monthly Data Summary:")
            for month_key, stats in sorted(monthly_stats.items()):
                logger.info(f"  {month_key}: {stats['cycles']} cycles, {stats['total_records']} records, {stats['total_anomalies']} anomalies")
        else:
            logger.info("No cycles found in database.")
            
        # Get billing codes summary
        db.db.cursor.execute("SELECT COUNT(*) FROM billing_codes")
        total_codes = db.db.cursor.fetchone()[0]
        logger.info(f"Total unique billing codes: {total_codes}")
        
        del db
        
    except Exception as e:
        logger.error(f"Failed to get database summary: {e}")

def create_output_directories():
    """Create necessary output directories."""
    directories = [
        "data/Anomalies"  # Only keep anomaly reports for analysts
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def main():
    """Main clean demo execution."""
    logger.info("=" * 60)
    logger.info("Clean Telecom Billing Anomaly Detection Demo")
    logger.info("=" * 60)
    
    # Step 1: Check dependencies
    logger.info("\nStep 1: Checking dependencies...")
    if not check_dependencies():
        logger.error("Dependency check failed. Please install missing packages.")
        return False
    
    # Step 2: Create output directories
    logger.info("\nStep 2: Creating output directories...")
    create_output_directories()
    
    # Step 3: Set up database
    logger.info("\nStep 3: Setting up database...")
    if not setup_database():
        logger.error("Database setup failed.")
        return False
    
    # Step 4: Generate and store 30 cycles
    logger.info("\nStep 4: Generating and storing 30 cycles...")
    if not generate_and_store_30_cycles():
        logger.error("Cycle generation and storage failed.")
        return False
    
    # Step 5: Run anomaly detection demo on 2 cycles
    logger.info("\nStep 5: Running anomaly detection demo...")
    if not run_anomaly_detection_demo(num_cycles=2):
        logger.error("Anomaly detection demo failed.")
        return False
    
    # Step 6: Show database summary
    logger.info("\nStep 6: Database summary...")
    show_database_summary()
    
    # Step 7: Show output files
    logger.info("\nStep 7: Output files created:")
    anomaly_files = os.listdir("data/Anomalies") if os.path.exists("data/Anomalies") else []
    for file in anomaly_files:
        if file.endswith('.xlsx'):
            logger.info(f"  data/Anomalies/{file}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Clean demo completed successfully!")
    logger.info("=" * 60)
    logger.info("\nProject Structure:")
    logger.info("├── billing_anomaly_detection.db (SQLite database with all data)")
    logger.info("├── data/Anomalies/ (Excel reports for analysts)")
    logger.info("├── data/sample_data/ (Generated sample files)")
    logger.info("├── data/descriptions/ (Code description files)")
    logger.info("├── *.py (Core processing scripts)")
    logger.info("└── *.md (Documentation)")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Demo failed with unexpected error: {e}")
        sys.exit(1) 