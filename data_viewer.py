import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Dummy Data Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📊 Dummy Data Viewer")
st.markdown("View and explore the generated dummy billing data")

# Check if data directory exists
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    st.error(f"Data directory '{DATA_DIR}' not found. Please run the data generation script first.")
    st.stop()

# Sidebar for navigation
st.sidebar.title("Navigation")
view_mode = st.sidebar.selectbox(
    "Select View Mode",
    ["Overview", "Billing Cycle Data", "Code Descriptions", "Charts & Analytics", "Data Export"]
)

# Helper function to load Excel files
def load_excel_file(file_path, sheet_name=None):
    try:
        if sheet_name:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return None

# Overview Mode
if view_mode == "Overview":
    st.header("📋 Data Overview")
    
    # List available files
    st.subheader("Available Data Files")
    
    billing_file = os.path.join(DATA_DIR, "Sample_Billing_Cycle.xlsx")
    if os.path.exists(billing_file):
        st.success("✅ Sample_Billing_Cycle.xlsx found")
        
        # Show sheet information
        try:
            excel_file = pd.ExcelFile(billing_file)
            st.write("**Sheets in billing cycle file:**")
            for sheet in excel_file.sheet_names:
                df = pd.read_excel(billing_file, sheet_name=sheet)
                st.write(f"- {sheet}: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            st.error(f"Error reading billing file: {str(e)}")
    else:
        st.error("❌ Sample_Billing_Cycle.xlsx not found")
    
    # Check description files
    desc_files = [
        "Single_Event_Charges_Descriptions.xlsx",
        "Account_Corrections_Descriptions.xlsx"
    ]
    
    st.write("**Description files:**")
    for desc_file in desc_files:
        file_path = os.path.join(DATA_DIR, desc_file)
        if os.path.exists(file_path):
            st.success(f"✅ {desc_file}")
        else:
            st.warning(f"⚠️ {desc_file} not found")

# Billing Cycle Data Mode
elif view_mode == "Billing Cycle Data":
    st.header("📈 Billing Cycle Data")
    
    billing_file = os.path.join(DATA_DIR, "Sample_Billing_Cycle.xlsx")
    if not os.path.exists(billing_file):
        st.error("Billing cycle file not found. Please run the data generation script first.")
        st.stop()
    
    # Load all sheets
    try:
        excel_file = pd.ExcelFile(billing_file)
        sheet_names = excel_file.sheet_names
        
        # Sheet selector
        selected_sheet = st.selectbox("Select Sheet", sheet_names)
        
        if selected_sheet:
            df = pd.read_excel(billing_file, sheet_name=selected_sheet)
            
            st.subheader(f"Data from '{selected_sheet}' sheet")
            
            # Show basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
            
            # Show data
            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)
            
            # Show statistics
            st.subheader("Statistical Summary")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            
            # Show column info
            st.subheader("Column Information")
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null Count': df.count(),
                'Null Count': df.isnull().sum()
            })
            st.dataframe(col_info, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading billing cycle data: {str(e)}")

# Code Descriptions Mode
elif view_mode == "Code Descriptions":
    st.header("📝 Code Descriptions")
    
    desc_files = [
        ("Single Event Charges", "Single_Event_Charges_Descriptions.xlsx"),
        ("Account Corrections", "Account_Corrections_Descriptions.xlsx")
    ]
    
    for title, filename in desc_files:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            st.subheader(title)
            df = load_excel_file(file_path)
            if df is not None:
                st.dataframe(df, use_container_width=True)
                
                # Show code distribution
                if 'Billing_CODE' in df.columns:
                    st.write(f"**Total Codes:** {len(df)}")
                    
                    # Show first few characters of codes
                    if len(df) > 0:
                        code_prefixes = df['Billing_CODE'].str[:3].value_counts()
                        st.write("**Code Prefixes:**")
                        st.write(code_prefixes)
        else:
            st.warning(f"File {filename} not found")

# Charts & Analytics Mode
elif view_mode == "Charts & Analytics":
    st.header("📊 Charts & Analytics")
    
    billing_file = os.path.join(DATA_DIR, "Sample_Billing_Cycle.xlsx")
    if not os.path.exists(billing_file):
        st.error("Billing cycle file not found. Please run the data generation script first.")
        st.stop()
    
    try:
        # Load all sheets for analysis
        excel_file = pd.ExcelFile(billing_file)
        
        # Combine all sheets for analysis
        all_data = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(billing_file, sheet_name=sheet_name)
            df['Sheet_Name'] = sheet_name
            all_data.append(df)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        st.subheader("Data Overview")
        
        # Chart 1: Data distribution by sheet
        fig1 = px.bar(
            x=combined_df['Sheet_Name'].value_counts().index,
            y=combined_df['Sheet_Name'].value_counts().values,
            title="Number of Records by Sheet",
            labels={'x': 'Sheet Name', 'y': 'Number of Records'}
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Chart 2: Monthly data distribution
        if 'Month' in combined_df.columns:
            monthly_counts = combined_df['Month'].value_counts().sort_index()
            fig2 = px.bar(
                x=monthly_counts.index,
                y=monthly_counts.values,
                title="Data Distribution by Month",
                labels={'x': 'Month', 'y': 'Number of Records'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Chart 3: Year distribution
        if 'Year' in combined_df.columns:
            year_counts = combined_df['Year'].value_counts().sort_index()
            fig3 = px.pie(
                values=year_counts.values,
                names=year_counts.index,
                title="Data Distribution by Year"
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        # Chart 4: Bill cycle distribution
        if 'Bill Cycle Number' in combined_df.columns:
            cycle_counts = combined_df['Bill Cycle Number'].value_counts().sort_index()
            fig4 = px.bar(
                x=cycle_counts.index,
                y=cycle_counts.values,
                title="Data Distribution by Bill Cycle",
                labels={'x': 'Bill Cycle Number', 'y': 'Number of Records'}
            )
            st.plotly_chart(fig4, use_container_width=True)
        
        # Time series analysis for monthly data
        st.subheader("Monthly Data Trends")
        
        # Get columns that represent months
        month_columns = [col for col in combined_df.columns if 'Months_ago' in col or col == 'Active Month']
        
        if month_columns:
            # Calculate average values for each month
            monthly_avg = {}
            for col in month_columns:
                monthly_avg[col] = combined_df[col].mean()
            
            fig5 = px.line(
                x=list(monthly_avg.keys()),
                y=list(monthly_avg.values()),
                title="Average Values by Month",
                labels={'x': 'Month', 'y': 'Average Value'}
            )
            st.plotly_chart(fig5, use_container_width=True)
        
        # Correlation heatmap for numeric columns
        st.subheader("Correlation Analysis")
        numeric_df = combined_df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            fig6 = px.imshow(
                corr_matrix,
                title="Correlation Heatmap",
                color_continuous_scale='RdBu'
            )
            st.plotly_chart(fig6, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating charts: {str(e)}")

# Data Export Mode
elif view_mode == "Data Export":
    st.header("💾 Data Export")
    
    st.subheader("Download Generated Data")
    
    # List all files in data directory
    data_files = []
    if os.path.exists(DATA_DIR):
        for file in os.listdir(DATA_DIR):
            if file.endswith('.xlsx'):
                data_files.append(file)
    
    if data_files:
        st.write("**Available files for download:**")
        
        for file in data_files:
            file_path = os.path.join(DATA_DIR, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {file}")
            with col2:
                st.write(f"{file_size:.1f} KB")
            with col3:
                with open(file_path, 'rb') as f:
                    st.download_button(
                        label="Download",
                        data=f.read(),
                        file_name=file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    else:
        st.warning("No Excel files found in the data directory.")
    
    st.subheader("Export Options")
    
    # Option to regenerate data
    if st.button("🔄 Regenerate Sample Data"):
        try:
            import subprocess
            result = subprocess.run(['python', 'generate_sample_data.py'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ Sample data regenerated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Error regenerating data: {result.stderr}")
        except Exception as e:
            st.error(f"❌ Error running data generation script: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*Data Viewer created for dummy data generation output*")