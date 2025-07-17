# Telecom Billing Anomaly Detection & Analytics Engine

## Overview
This project automates the extraction, transformation, and anomaly detection of telecom billing data from multi-sheet Excel files. It is designed to replicate and improve upon a real-world process used at a major wireless carrier, enabling analysts and managers to quickly identify unusual billing activity and generate audit-ready reports.

- **Automated data ingestion** from complex Excel files
- **Feature engineering** for robust anomaly detection
- **Business-rule-based anomaly flagging**
- **Output of both anomaly reports and full cycle tables**
- **Sample data generation script included**

For a detailed breakdown of the project architecture and development plan, see [ARCHITECTURE.md](./ARCHITECTURE.md) and [DEVELOPMENTPLAN.md](./DEVELOPMENTPLAN.md).

---

## Project Structure

```
Alexander Wireless/
  anomaly_detection.py         # Main processing script
  generate_sample_data.py      # Script to generate sample Excel files
  requirements.txt             # Python dependencies
  ARCHITECTURE.md              # Detailed architecture and business logic
  DEVELOPMENTPLAN.md           # Step-by-step development plan
  README.md                    # This file
  /data/                       # Input Excel files (generated)
  /output/                     # Generated reports and tables
```

---

## Setup Instructions

1. **Clone the repository and navigate to the project directory.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Generate sample data (optional, for testing):**
   ```bash
   python generate_sample_data.py
   ```
   This will create sample billing cycle and code description files in `/data/`.
4. **Run the main anomaly detection script:**
   ```bash
   python anomaly_detection.py
   ```
   Outputs will be saved in `/output/`.

---

## Usage
- Place your billing cycle Excel file(s) and code description file(s) in the `/data/` directory.
- Run the main script to process the data and generate outputs.
- Review the anomaly report and full cycle table in `/output/`.

---

## Documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md):** Full technical and business process documentation.
- **[DEVELOPMENTPLAN.md](./DEVELOPMENTPLAN.md):** Step-by-step implementation plan.

---

## Author & Contact
Created by Dylan Alexander Knox. For questions or collaboration, please contact [your email or GitHub profile]. 