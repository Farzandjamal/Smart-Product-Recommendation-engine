import streamlit as st
import pandas as pd
import json
import requests
from rapidfuzz import process, fuzz

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    path = 'flipkart_small.csv'
    try:
        df = pd.read_csv(path, encoding='Latin-1')
        # Clean column names to remove hidden spaces
        df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

    df.drop(['crawl_timestamp','product_url','overall_rating','is_FK_Advantage_product'], axis=1, inplace=True, errors='ignore')
    df['brand'] = df['brand'].fillna('unknown')
    df['retail_price'] = df['retail_price'].fillna(0)
    df['image'] = df['image'].fillna('')
    df = df.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)
    return df

df = load_data()

# --- 2. THE IMAGE RESOLVER (Enhanced) ---
def get_image_url(img_data):
    # 1. Check if empty
    if not img_data or str(img_data).strip() == "" or str(img_data) == '[]':
        return "https://via.placeholder.com/150?text=No+Image+Available"
    
    try:
        # 2. Clean the string (Flipkart stores images as ["link1", "link2"])
        clean_str = str(img_data).strip()
        if clean_str.startswith("["):
            # Remove brackets and quotes manually (safest way)
            url = clean_str.replace('[', '').replace(']', '').replace('"', '').replace("'", "").split(',')[0].strip()
        else:
            url = clean_str

        # 3. Handle relative paths or bad starts
        if not url.startswith("http"):
            return "https://via.placeholder.com/150?text=Invalid+URL"

        # 4. Force HTTPS (Crucial for Streamlit Cloud)
        url = url.replace("http://", "https://")
        return url
    except:
        return "https://via.placeholder.com/150?text=Error+Loading"

# --- 3. RECOMMENDATION LOGIC ---
def get_smart_recommendations(user_input, max_items=8):
    query = user_input.lower().strip()
    if not query: return None

    # Exact/Partial Match
    mask = df['product_name'].str.lower().str.contains(query, na=False) | \
           df['brand'].str.lower().str.contains(query, na=False)
    combined = df[mask].copy()

    # Fuzzy Match Fallback
    if combined.empty:
        all_names = df['product_name'].tolist()
        match = process.extractOne(query, all_names, scorer=fuzz.token_set_ratio)
        if match and match[1] > 70:
            combined = df[df['product_name'] == match[0]].copy()
        else: return None
    
    return combined.head(max_items)

# --- 4. STREAMLIT UI ---
st.set_page_config(layout="wide", page_title="Flipkart Search")
st.title("🛒 Smart Recommendation Engine")

with st.form("search_form"):
    user_query = st.text_input("Search for a product:", placeholder="e.g. Watch, Bag, Shirt")
    submit = st.form_submit_button("Search", type='primary')

if submit and user_query:
    results = get_smart_recommendations(user_query)
    
    if results is not None and not results.empty:
        cols = st.columns(4) 
        for i, (idx, row) in enumerate(results.iterrows()):
            with cols[i % 4]:
                # Get cleaned URL
                img_url = get_image_url(row['image'])
                
                # Display Image
                st.image(img_url, use_container_width=True)
                
                # Display Info
                st.write(f"**{row['product_name'][:50]}...**")
                st.success(f"₹{row['retail_price']}")
                
                # DEBUG OPTION: Uncomment line below if pics still don't show
                # st.caption(f"Source: {img_url[:30]}...") 
    else:
        st.warning("No products found.")
