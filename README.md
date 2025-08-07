# Telecom Billing Anomaly Detection & Analytics Engine

## Overview
This project automates the extraction, transformation, and anomaly detection of telecom billing data from multi-sheet Excel files. It is designed to replicate and improve upon a real-world process used at a major wireless carrier, enabling analysts and managers to quickly identify unusual billing activity and generate audit-ready reports.

- **Automated data ingestion** from complex Excel files
- **Feature engineering** for robust anomaly detection
- **Business-rule-based anomaly flagging**
- **SQLite database storage** for all processed data
- **Anomaly reports for analyst review**
- **Sample data generation script included**
- **One-click demo script for streamlined setup and demonstration**

For a detailed breakdown of the project architecture and development plan, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Project Structure

```
Alexander Wireless/
  billing_anomaly_detection.db    # SQLite database (all data)
  run_clean_demo.py               # One-click demo script
  database_setup.py               # Database initialization
  database_integration.py         # Database operations
  anomaly_detection_with_db.py    # Main processing with DB integration
  generate_extended_sample_data.py # Generate 30 cycles of sample data
  anomaly_detection_next_month.py # Process next month cycles
  database_queries.py             # Advanced database analysis
  requirements.txt                # Python dependencies
  ARCHITECTURE.md                 # Detailed architecture and business logic
  README.md                       # This file
  /data/                          # Input and output files
    /sample_data/                 # Generated sample Excel files
    /descriptions/                # Code description files
    /Anomalies/                   # Excel reports for analysts
```

---

## Quick Start: One-Click Demo

1. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Run the clean demo script:**
   ```bash
   python run_clean_demo.py
   ```
   This script will:
   - Set up the SQLite database
   - Generate 30 cycles of sample data across 3 months
   - Store all data in the database
   - Run anomaly detection on 2 cycles (for demo)
   - Generate Excel reports for analyst review

3. **View results:**
   - Anomaly reports: `data/Anomalies/`
   - Database: `billing_anomaly_detection.db`
   - Sample data: `data/sample_data/`

---

## Database Integration
- All processed billing data is stored in SQLite database
- Includes all codes regardless of anomaly thresholds
- Tracks processing history and configuration
- Enables historical analysis and trend tracking

---

## Key Features

### Data Processing
- **30 cycles generated** across 3 sequential months
- **Random cycle numbers 1-30** in sequential order per month
- **All data stored in SQLite** for analysis
- **Anomaly detection on subset** for demo efficiency

### Anomaly Detection
- **Z-score analysis** for statistical outliers
- **Percent change thresholds** by bill type
- **Special case flagging** (new codes, drops to zero)
- **Excel reports** for analyst review

### Database Features
- **Complete data storage** (not just anomalies)
- **Processing history tracking**
- **Configuration management**
- **Advanced query capabilities**

---

## Usage

### For Analysts
- Review anomaly reports in `data/Anomalies/`
- Use database queries for historical analysis
- Track billing code performance over time

### For Developers
- Add new bill types or codes
- Modify anomaly detection thresholds
- Extend database schema as needed

---

## Troubleshooting
- **pip not recognized:** Use `python -m pip install -r requirements.txt`
- **Database errors:** Delete `billing_anomaly_detection.db` and re-run demo
- **Missing files:** Ensure all dependencies are installed

---

## Documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md):** Full technical and business process documentation.

---

## Author & Contact
Created by Dylan Alexander Knox. For questions or collaboration, please contact dylan.knox2000@gmail.com or https://github.com/daknox. 