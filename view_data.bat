@echo off
echo ========================================
echo Telecom Billing Database Viewer
echo ========================================
echo.

echo Checking for database file...
if exist "billing_anomaly_detection.db" (
    echo ✅ Database found: billing_anomaly_detection.db
    echo    Size: 
    dir billing_anomaly_detection.db | findstr "billing_anomaly_detection.db"
) else (
    echo ❌ Database file not found!
    goto :end
)

echo.
echo Checking for Excel files...
if exist "data\Anomalies\*.xlsx" (
    echo ✅ Found Excel anomaly reports:
    dir "data\Anomalies\*.xlsx" /b
) else (
    echo ❌ No Excel files found in data\Anomalies\
)

echo.
echo ========================================
echo FREE VIEWING OPTIONS:
echo ========================================
echo.
echo 📊 FOR DATABASE (.db file):
echo   1. Download DB Browser for SQLite (FREE)
echo      https://sqlitebrowser.org/
echo   2. Open billing_anomaly_detection.db with it
echo.
echo 📈 FOR EXCEL FILES (.xlsx):
echo   1. Upload to Google Drive → Open in Google Sheets
echo   2. Download LibreOffice Calc (FREE)
echo      https://www.libreoffice.org/
echo   3. Use online Excel viewers:
echo      - Office Online (free with Microsoft account)
echo      - Zoho Sheet (free tier)
echo.
echo 📋 QUICK VIEW:
echo   - Open any .xlsx file in a text editor (will show XML)
echo   - Use Notepad++ or VS Code for better viewing
echo.
echo ========================================
echo Files you can view:
echo ========================================
echo.
echo Database: billing_anomaly_detection.db (5.7MB)
echo Excel Reports: data\Anomalies\*.xlsx (15 files)
echo.
echo Press any key to exit...
pause >nul

:end 