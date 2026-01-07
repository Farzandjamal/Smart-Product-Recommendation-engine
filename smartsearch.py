import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from rapidfuzz import process, fuzz

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('flipkart_small.csv', encoding='Latin-1')
        df.columns = df.columns.str.strip()
        df['image'] = df['image'].fillna('')
        df['retail_price'] = pd.to_numeric(df['retail_price'], errors='coerce').fillna(0)
        return df.drop_duplicates(subset=['product_name'])
    except:
        return pd.DataFrame()

df = load_data()

# --- 2. IMAGE PROXY LOGIC ---
@st.cache_data(show_spinner=False)
def fetch_image_bytes(img_data):
    """Downloads the image on the server side to bypass browser blocks."""
    if not img_data or img_data == '[]':
        return "https://via.placeholder.com/150?text=No+Data"
    
    try:
        # Clean string to get URL
        url = str(img_data).strip('[]').replace('"', '').replace("'", "").split(',')[0].strip()
        url = url.replace("http://", "https://") # Try HTTPS first
        
        # Request the image as bytes
        response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return response.content # Return raw bytes
    except:
        pass
    return "https://via.placeholder.com/150?text=Link+Expired"

# --- 3. RECOMMENDATION LOGIC ---
def get_recs(query):
    query = query.lower().strip()
    mask = df['product_name'].str.lower().str.contains(query, na=False)
    res = df[mask].copy()
    
    if res.empty:
        names = df['product_name'].tolist()
        match = process.extractOne(query, names, scorer=fuzz.token_set_ratio)
        if match and match[1] > 70:
            res = df[df['product_name'] == match[0]].copy()
        else: return None
    return res.head(8)

# --- 4. UI ---
st.set_page_config(layout="wide")
st.title("🛒 Smart Recommendation Engine")

query = st.text_input("Search Flipkart Products:", placeholder="Watch, Bag, Shoes...")

if query:
    results = get_recs(query)
    if results is not None:
        cols = st.columns(4)
        for i, (idx, row) in enumerate(results.iterrows()):
            with cols[i % 4]:
                # IMAGE DISPLAY
                img_source = fetch_image_bytes(row['image'])
                st.image(img_source, use_container_width=True)
                
                # PRODUCT INFO
                st.write(f"**{row['product_name'][:45]}...**")
                st.info(f"Price: ₹{int(row['retail_price'])}")
    else:
        st.warning("No products found.")
