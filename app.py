import streamlit as st
import pandas as pd
import numpy as np

st.title("📈 Amazon Ads Optimizer")

# Upload 3 CSVs
st.subheader("Step 1: Upload your 3 campaign export files")
file1 = st.file_uploader("📁 Upload file for Date 1", type="csv", key="date1")
file2 = st.file_uploader("📁 Upload file for Date 2", type="csv", key="date2")
file3 = st.file_uploader("📁 Upload file for Date 3", type="csv", key="date3")

if file1 and file2 and file3:
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df3 = pd.read_csv(file3)
    
# Validate structure
expected_columns = ['Keyword', 'Match type', 'Impressions', 'Clicks', 'Spend(EUR)', 
                    'Sales(EUR)', 'Orders', 'CTR', 'CPC(EUR)', 'ACOS', 'ROAS']

def validate_file(df, label):
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        st.error(f"❌ '{label}' is missing columns: {missing}")
        return False
    return True

if not (validate_file(df1, 'Date 1') and validate_file(df2, 'Date 2') and validate_file(df3, 'Date 3')):
    st.stop()

# ✅ Now all this below runs if validation passes — outside the if-block
columns_to_keep = ['Keyword', 'Match type', 'Impressions', 'Clicks', 'Spend(EUR)', 
                   'Sales(EUR)', 'Orders', 'CTR', 'CPC(EUR)', 'ACOS', 'ROAS']

def clean_dataset(df, period):
    df = df[columns_to_keep].copy()
    df['Period'] = period
    return df

df1_clean = clean_dataset(df1, 'date1')
df2_clean = clean_dataset(df2, 'date2')
df3_clean = clean_dataset(df3, 'date3')

combined_df = pd.concat([df1_clean, df2_clean, df3_clean], ignore_index=True)

grouped = combined_df.groupby(['Keyword', 'Match type', 'Period']).agg({
    'Impressions': 'sum',
    'Clicks': 'sum',
    'Spend(EUR)': 'sum',
    'Sales(EUR)': 'sum',
    'Orders': 'sum'
}).reset_index()

grouped['CTR'] = grouped['Clicks'] / grouped['Impressions'].replace(0, np.nan)
grouped['CPC(EUR)'] = grouped['Spend(EUR)'] / grouped['Clicks'].replace(0, np.nan)
grouped['ACOS'] = grouped['Spend(EUR)'] / grouped['Sales(EUR)'].replace(0, np.nan)
grouped['ROAS'] = grouped['Sales(EUR)'] / grouped['Spend(EUR)'].replace(0, np.nan)

metrics_to_pivot = ['CTR', 'ACOS', 'ROAS', 'CPC(EUR)', 'Impressions', 'Clicks', 'Spend(EUR)', 'Sales(EUR)', 'Orders']

pivoted = grouped.pivot_table(
    index=['Keyword', 'Match type'],
    columns='Period',
    values=metrics_to_pivot
)
pivoted.columns = [f'{metric}_{period}' for metric, period in pivoted.columns]
pivoted = pivoted.reset_index()

# Ensure required columns exist to avoid KeyErrors
required_columns = [
    'CTR_date1', 'CTR_date2', 'CTR_date3',
    'ACOS_date1', 'ACOS_date2', 'ACOS_date3',
    'ROAS_date1', 'ROAS_date2', 'ROAS_date3',
    'Orders_date3', 'Clicks_date3', 'Spend(EUR)_date3', 'Impressions_date3'
]

for col in required_columns:
    if col not in pivoted.columns:
        pivoted[col] = np.nan

# Metrics
pivoted['CTR_change_date3_vs_date2'] = pivoted['CTR_date3'] - pivoted['CTR_date2']
pivoted['CTR_change_date3_vs_date1'] = pivoted['CTR_date3'] - pivoted['CTR_date1']
pivoted['ACOS_change_date3_vs_date2'] = pivoted['ACOS_date3'] - pivoted['ACOS_date2']
pivoted['ACOS_change_date3_vs_date1'] = pivoted['ACOS_date3'] - pivoted['ACOS_date1']
pivoted['ROAS_change_date3_vs_date2'] = pivoted['ROAS_date3'] - pivoted['ROAS_date2']
pivoted['ROAS_change_date3_vs_date1'] = pivoted['ROAS_date3'] - pivoted['ROAS_date1']

pivoted['CR_date3'] = pivoted['Orders_date3'] / pivoted['Clicks_date3'].replace(0, np.nan)
pivoted['CPC_date3'] = pivoted['Spend(EUR)_date3'] / pivoted['Clicks_date3'].replace(0, np.nan)

def classify_keyword(row):
    if row['Sales(EUR)_date3'] < 1 and row['Clicks_date3'] >= 10:
        return 'CUT'
    if row['ROAS_date3'] > 2.0 and row['ROAS_change_date3_vs_date2'] > 0 and row['ACOS_date3'] < 0.4:
        return 'INCREASE'
    if row['CTR_change_date3_vs_date2'] > 0 and row['ROAS_change_date3_vs_date2'] > 0:
        return 'OPTIMIZE'
    if row['Spend(EUR)_date3'] > 10 and row['Orders_date3'] == 0:
        return 'PAUSE'
    if row['CTR_date3'] < 0.002 and row['Impressions_date3'] > 1000:
        return 'REMOVE'
    if row['CR_date3'] > 0.15 and row['CPC_date3'] < 0.3:
        return 'BOOST'
    return 'REVIEW'

pivoted['Recommendation'] = pivoted.apply(classify_keyword, axis=1)

st.subheader("✅ Recommendations Table")
selected = st.multiselect("Filter by Recommendation", options=pivoted['Recommendation'].unique().tolist(), default=list(pivoted['Recommendation'].unique()))
st.dataframe(pivoted[pivoted['Recommendation'].isin(selected)])

st.download_button("⬇️ Download CSV", data=pivoted.to_csv(index=False), file_name="campaign_recommendations.csv")
