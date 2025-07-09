import streamlit as st
import pandas as pd
import numpy as np

# --- TITLE ---
st.title("📈 Amazon Ads Optimizer")

# 🅐 SESSION NAME
session_name = st.text_input("📌 Session Name", value="Amazon Optimization Session")

# 🅑 PRODUCT INFO
st.subheader("📝 Product Listing Info (optional)")
product_title = st.text_area("Product Title", value="none")
product_bullets = st.text_area("Bullet Points (paste all)", value="none")
product_description = st.text_area("Product Description", value="none")

# 🅒 NEW KEYWORDS
new_keywords_raw = st.text_area("🧪 New Keyword Ideas (one per line)", value="")
new_keywords = [kw.strip() for kw in new_keywords_raw.split("\n") if kw.strip()]

# 🅓 CAMPAIGN FILE UPLOAD
st.subheader("📁 Upload Your 3 Amazon Ads Campaign Exports")
file1 = st.file_uploader("Date 1", type="csv", key="date1")
file2 = st.file_uploader("Date 2", type="csv", key="date2")
file3 = st.file_uploader("Date 3", type="csv", key="date3")

# --- VALIDATION + NORMALIZATION ---
expected_columns = ['Keyword', 'Match type', 'Impressions', 'Clicks', 'Spend',
                    'Sales', 'Orders', 'CTR', 'CPC', 'ACOS', 'ROAS']

def validate_file(df, label):
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        st.error(f"❌ '{label}' is missing columns: {missing}")
        return False
    return True

def standardize_currency_columns(df):
    if 'Spend(EUR)' in df.columns:
        df = df.rename(columns={
            'Spend(EUR)': 'Spend',
            'Sales(EUR)': 'Sales',
            'CPC(EUR)': 'CPC'
        })
    elif 'Spend(USD)' in df.columns:
        df = df.rename(columns={
            'Spend(USD)': 'Spend',
            'Sales(USD)': 'Sales',
            'CPC(USD)': 'CPC'
        })
    else:
        st.error("❌ Missing expected currency columns (Spend(EUR) or Spend(USD))")
        st.stop()
    return df

# --- PLACEHOLDER AI-LIKE ADVICE FUNCTION ---
def generate_ai_advice(row):
    if row['Sales_date3'] < 1 and row['Clicks_date3'] >= 10:
        return "High clicks, no sales – likely a relevance issue."
    if row['ROAS_date3'] > 2:
        return "Great ROAS – consider scaling this keyword."
    if row['CTR_date3'] < 0.002:
        return "Low CTR – test rewriting product title or image."
    if row['ACOS_date3'] > 0.6:
        return "High ACOS – test lower bid or negative targeting."
    return "Mixed performance – monitor and adjust if needed."

def generate_listing_optimization(title, bullets, description):
    return f"""
### Optimized Title
{title if title != 'none' else '[No title provided]'}

### Optimized Bullet Points
1. Emphasize benefits, not just features
2. Use keywords naturally
3. Include dimensions or compatibility
4. Add a strong CTA like “Buy Now”
5. Mention guarantees or differentiators

### Optimized Description
{description if description != 'none' else '[No description provided]'}\n\n
Tip: Expand this into a compelling story with emotional and practical hooks.
"""

# --- MAIN LOGIC ---
if file1 and file2 and file3:
    df1 = standardize_currency_columns(pd.read_csv(file1))
    df2 = standardize_currency_columns(pd.read_csv(file2))
    df3 = standardize_currency_columns(pd.read_csv(file3))

    if not (validate_file(df1, 'Date 1') and validate_file(df2, 'Date 2') and validate_file(df3, 'Date 3')):
        st.stop()

    columns_to_keep = ['Keyword', 'Match type', 'Impressions', 'Clicks', 'Spend',
                       'Sales', 'Orders', 'CTR', 'CPC', 'ACOS', 'ROAS']

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
        'Spend': 'sum',
        'Sales': 'sum',
        'Orders': 'sum'
    }).reset_index()

    grouped['CTR'] = grouped['Clicks'] / grouped['Impressions'].replace(0, np.nan)
    grouped['CPC'] = grouped['Spend'] / grouped['Clicks'].replace(0, np.nan)
    grouped['ACOS'] = grouped['Spend'] / grouped['Sales'].replace(0, np.nan)
    grouped['ROAS'] = grouped['Sales'] / grouped['Spend'].replace(0, np.nan)

    metrics_to_pivot = ['CTR', 'ACOS', 'ROAS', 'CPC', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']

    pivoted = grouped.pivot_table(
        index=['Keyword', 'Match type'],
        columns='Period',
        values=metrics_to_pivot
    )
    pivoted.columns = [f'{metric}_{period}' for metric, period in pivoted.columns]
    pivoted = pivoted.reset_index()

    required_columns = [
        'CTR_date1', 'CTR_date2', 'CTR_date3',
        'ACOS_date1', 'ACOS_date2', 'ACOS_date3',
        'ROAS_date1', 'ROAS_date2', 'ROAS_date3',
        'Orders_date3', 'Clicks_date3', 'Spend_date3', 'Impressions_date3', 'Sales_date3'
    ]

    for col in required_columns:
        if col not in pivoted.columns:
            pivoted[col] = np.nan

    pivoted['CTR_change_date3_vs_date2'] = pivoted['CTR_date3'] - pivoted['CTR_date2']
    pivoted['CTR_change_date3_vs_date1'] = pivoted['CTR_date3'] - pivoted['CTR_date1']
    pivoted['ACOS_change_date3_vs_date2'] = pivoted['ACOS_date3'] - pivoted['ACOS_date2']
    pivoted['ACOS_change_date3_vs_date1'] = pivoted['ACOS_date3'] - pivoted['ACOS_date1']
    pivoted['ROAS_change_date3_vs_date2'] = pivoted['ROAS_date3'] - pivoted['ROAS_date2']
    pivoted['ROAS_change_date3_vs_date1'] = pivoted['ROAS_date3'] - pivoted['ROAS_date1']

    pivoted['CR_date3'] = pivoted['Orders_date3'] / pivoted['Clicks_date3'].replace(0, np.nan)
    pivoted['CPC_date3'] = pivoted['Spend_date3'] / pivoted['Clicks_date3'].replace(0, np.nan)

    pivoted['AI_Advice'] = pivoted.apply(generate_ai_advice, axis=1)

    # --- DISPLAY RESULTS ---
    st.subheader("📊 Recommendations Table")
    selected = st.multiselect("Filter by Keyword", options=pivoted['Keyword'].unique(), default=pivoted['Keyword'].unique())
    st.dataframe(pivoted[pivoted['Keyword'].isin(selected)])

    st.download_button("⬇️ Download Recommendations CSV", data=pivoted.to_csv(index=False), file_name=f"{session_name}_recommendations.csv")

    # --- LISTING GENERATION (STATIC) ---
    st.subheader("🪄 Suggested Listing Optimization")
    st.markdown(generate_listing_optimization(product_title, product_bullets, product_description))

    # --- NEW KEYWORDS ---
    if new_keywords:
        st.subheader("🧪 New Keyword Suggestions")
        for kw in new_keywords:
            st.markdown(f"**{kw}** — consider launching with exact match, low bid, and monitor ROAS")
