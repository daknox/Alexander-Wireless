# ARCHITECTURE.md

## Project: Telecom Billing Anomaly Detection & Analytics Engine

### Author: Dylan Alexander Knox

---

## 1. Project Purpose & Business Context

This project is a full-scale, end-to-end recreation of a telecom billing anomaly detection and reporting process originally built to address a real-world business challenge at a major wireless carrier. The primary business problem: **third-party billing vendors do not provide direct query access to detailed billing cycle data**, requiring analysts to work with large, multi-sheet Excel exports for each cycle.

**Key Goals:**
- Automate the extraction, transformation, and consolidation of billing data from multiple Excel sheets.
- Engineer features for robust anomaly detection and trend analysis.
- Replicate all business logic and outputs of the original process, including audit-ready anomaly reports and comprehensive cycle tables for analytics.
- Enable analysts and managers to quickly identify, research, and report on unusual billing activity.

---

## 2. Data Sources & Structure

### 2.1. Billing Cycle Excel File

- **Input:** One Excel file per billing cycle, containing at least 4 relevant sheets:
  - **Single Event Charges** (non-recurring, with code descriptions)
  - **Account Corrections** (adjustments, with code descriptions)
  - **Subscription Plans** (recurring monthly plans)
  - **Line Add-ons** (additional lines/features)

- **Each sheet contains:**
  - Billing codes (unique per type)
  - Amounts for the current and previous 5 months
  - Metadata: cycle number, year, month, bill type, etc.

### 2.2. Code Description Excel File

- **Purpose:** Provides human-readable descriptions for billing codes in "Single Event Charges" and "Account Corrections".
- **Join:** On billing code.

---

## 3. Data Pipeline: Step-by-Step Breakdown

### 3.1. Ingestion

- **Read** the 4 relevant sheets from the billing Excel file.
- **For "Single Event Charges" and "Account Corrections":**
  - **Join** in code descriptions from the external file.

### 3.2. Consolidation

- **Stack** all billing codes from all categories into a single unified table.
- **Add** a column to indicate the billing category (anonymized as "Audit Type").
- **Extract** and apply the billing cycle number and date to each row.

### 3.3. Feature Engineering

- **Calculate rolling averages** for each code over the previous 5 months.
- **Compute deltas and percent changes:**
  - Current vs. rolling average
  - Month-over-month (MoM) change
- **Flag special cases:**
  - **Drop to 0:** Code value drops to zero after being nonzero in prior months.
  - **New Code:** Code appears for the first time in the current cycle.

### 3.4. Anomaly Detection Logic

- **Apply business rules** (mirroring the original Alteryx logic):

  | Audit Type             | Absolute Change Threshold | Percent Change Threshold |
  |------------------------|--------------------------|-------------------------|
  | Single Event Charges   | 50,000                   | 25%                     |
  | Account Corrections    | 25,000                   | 25%                     |
  | Line Add-ons           | 25,000                   | 25%                     |
  | Subscription Plans     | 50,000                   | 25%                     |

- **Flag as anomaly if:**
  - (|Change| >= threshold AND |Change %| >= 25%)
  - OR the code is new this cycle
  - OR the code dropped to zero
  - OR the code is a "Grand Total" row

- **All logic is applied per row, using the "Audit Type" to select the correct thresholds.**

### 3.5. Output Generation

#### 3.5.1. Anomaly Report

- **Excel file** containing only rows flagged as anomalous.
- **Purpose:** For analyst review and research.
- **Fields included:** All engineered features, metadata, and flags.

#### 3.5.2. Full Cycle Table

- **Excel/CSV file** containing all codes, regardless of anomaly status.
- **Purpose:** For database ingestion (e.g., Snowflake), historical tracking, and dashboarding.
- **Fields included:** All engineered features, metadata, and flags.

---

## 4. Analyst Workflow & Applications

### 4.1. Anomaly Review

- **Analyst receives the anomaly report.**
- **Researches** flagged codes using the report and additional context in the "research file" (not automated, but supported by the output).
- **Documents findings** and root causes for each anomaly.

### 4.2. Historical Analysis

- **Full cycle table** is loaded into a database for:
  - Trend analysis across cycles and months.
  - Management reporting (e.g., monthly summaries, year-over-year comparisons).
  - Data visualization (e.g., Power BI, Tableau, or custom dashboards).

### 4.3. Management Reporting

- **Managers use the historical data** to:
  - Track overall billing trends.
  - Identify recurring issues or emerging patterns.
  - Communicate findings to leadership with data-driven insights.

---

## 5. Data Flow Diagram

```
[Billing Excel File]         [Code Description File]
         |                           |
         |                           |
         +-----------+   +-----------+
                     |   |
                 [Ingestion & Join]
                         |
                 [Consolidation]
                         |
                 [Feature Engineering]
                         |
                 [Anomaly Detection]
                         |
         +---------------+----------------+
         |                                |
 [Anomaly Report Output]         [Full Cycle Table Output]
         |                                |
   (Analyst Review)                (Database, Reporting)
```

---

## 6. Project Directory Structure

```
Alexander Wireless/
  anomaly_detection.py      # Main script for all processing
  ARCHITECTURE.md           # This document
  /data/                    # Input Excel files (billing cycles, code descriptions)
  /output/                  # Generated reports and tables
```

---

## 7. Key Business Rules (Alteryx Logic, Recreated)

- **For each row:**
  - If `Audit Type` is "Single Event Charges" or "Subscription Plans":
    - Flag as anomaly if (|Change| >= 50,000 AND |Change %| >= 25%) OR [New Code] OR [Drop To 0] OR [Code] = "Grand Total"
  - If `Audit Type` is "Account Corrections" or "Line Add-ons":
    - Flag as anomaly if (|Change| >= 25,000 AND |Change %| >= 25%) OR [New Code] OR [Drop To 0] OR [Code] = "Grand Total"
  - Else: Not flagged

- **All thresholds and logic are parameterized for easy adjustment.**

---

## 8. Limitations & Assumptions

- **Input files must follow a consistent structure** (sheet names, column names, etc.).
- **Descriptions are only joined for two categories** (Single Event Charges, Account Corrections).
- **Analyst research file** is not generated by this script, but the anomaly report is designed for easy copy-paste into that file.
- **No direct database or dashboard integration** is included in the current version.

---

## 9. How to Use

1. **Place the billing cycle Excel file(s) and code description file in the `/data/` directory.**
2. **Run `anomaly_detection.py`.**
3. **Find outputs in the `/output/` directory:**
   - `anomaly_report_<cycle>.xlsx`
   - `full_cycle_table_<cycle>.csv`
4. **Analysts review the anomaly report and use the full table for further analysis or database loading.**

---

## 10. Author & Motivation

Created by Dylan Alexander Knox to demonstrate advanced data engineering and analytics skills, based on a real-world process at a major telecom provider. This project is intended for portfolio display and graduate program applications.

---

## 11. Contact

For questions or collaboration, please contact [your email or GitHub profile]. 