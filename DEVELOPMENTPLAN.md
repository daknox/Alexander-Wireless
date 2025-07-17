# DEVELOPMENTPLAN.md

## Development Plan for Telecom Billing Anomaly Detection & Analytics Engine

This plan breaks down the architecture into actionable phases and tasks to guide the implementation of the project. Each phase includes specific deliverables and logical steps, ensuring a systematic approach from data ingestion to output generation.

---

## Phase 1: Project Setup & Data Ingestion

### 1.1. Repository & Directory Structure
- [ ] Create project directories: `/data/` for input files, `/output/` for results.
- [ ] Ensure `anomaly_detection.py` and documentation files are in place.

### 1.2. Input File Handling
- [ ] Implement logic to read Excel files from `/data/`.
- [ ] Identify and load the 4 relevant sheets: Single Event Charges, Account Corrections, Subscription Plans, Line Add-ons.
- [ ] Implement error handling for missing or malformed sheets.

### 1.3. Code Description Join
- [ ] Read code description Excel file.
- [ ] Join descriptions to Single Event Charges and Account Corrections sheets.

**Deliverables:**
- Script can load and join all required data sources.

---

## Phase 2: Data Consolidation & Preprocessing

### 2.1. Data Stacking
- [ ] Stack all billing codes from all categories into a single DataFrame/table.
- [ ] Add a column for "Audit Type" (billing category).

### 2.2. Metadata Extraction
- [ ] Extract billing cycle number and date from input files.
- [ ] Apply metadata to each row in the consolidated table.

### 2.3. Data Cleaning
- [ ] Ensure numeric columns are properly typed.
- [ ] Handle missing values and NaNs.

**Deliverables:**
- Clean, consolidated table with all required metadata.

---

## Phase 3: Feature Engineering

### 3.1. Rolling Calculations
- [ ] Calculate rolling averages for each code over the previous 5 months.

### 3.2. Delta & Percent Change
- [ ] Compute current vs. rolling average delta and percent change.
- [ ] Compute month-over-month (MoM) change and percent change.

### 3.3. Special Case Flags
- [ ] Flag "Drop to 0" cases.
- [ ] Flag "New Code" cases.

**Deliverables:**
- Table with all engineered features and flags.

---

## Phase 4: Anomaly Detection Logic

### 4.1. Business Rule Implementation
- [ ] Implement category-specific thresholds for absolute and percent change.
- [ ] Apply anomaly detection logic per row, using "Audit Type" to select thresholds.
- [ ] Flag anomalies based on business rules (including "Grand Total" rows).

**Deliverables:**
- Table with anomaly flags for each row.

---

## Phase 5: Output Generation

### 5.1. Anomaly Report
- [ ] Generate Excel file with only anomalous rows for analyst review.

### 5.2. Full Cycle Table
- [ ] Generate Excel/CSV file with all codes and engineered features for database ingestion and analytics.

**Deliverables:**
- `/output/anomaly_report_<cycle>.xlsx`
- `/output/full_cycle_table_<cycle>.csv`

---

## Phase 6: Documentation & Testing

### 6.1. Documentation
- [ ] Update `ARCHITECTURE.md` as needed.
- [ ] Document code and usage instructions.

### 6.2. Testing
- [ ] Create sample input files for testing.
- [ ] Validate outputs against expected results.
- [ ] Add error handling and edge case tests.

**Deliverables:**
- Fully documented and tested project ready for demonstration or extension.

---

## Optional/Future Phases
- Web UI for file upload
- Automated folder watcher
- Database integration
- Visualization scripts
- Advanced analytics (forecasting, clustering, etc.)

---

**This plan provides a step-by-step roadmap for building the project, ensuring clarity and completeness at each stage.** 