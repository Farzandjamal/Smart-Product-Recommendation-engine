import streamlit as st
import pandas as pd
import json
import requests
from io import BytesIO
from PIL import Image
from rapidfuzz import process, fuzz

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    path = r'flipkart_small.csv'
    df = pd.read_csv(path, encoding='Latin-1')
    df.drop(['crawl_timestamp','product_url','overall_rating','is_FK_Advantage_product'], axis=1, inplace=True, errors='ignore')
    df.drop_duplicates(inplace=True)
    df['brand'] = df['brand'].fillna('unknown')
    df['retail_price'] = df['retail_price'].fillna(df['retail_price'].median())
    df['image'] = df['image'].fillna('')
    df = df.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)
    return df

df = load_data()

# --- 2. THE LOGIC ---
def auto_clean(text):
    if not isinstance(text, str): return ""
    return text.lower().strip()

def get_image_url(img_data):
    """
    ULTIMATE FIX: Downloads the image using a Browser Header
    to bypass security blocks that prevent direct linking.
    """
    try:
        if not img_data or img_data == "" or img_data == "[]":
            return "https://via.placeholder.com/150"
            
        # 1. Clean the string to get the URL
        if isinstance(img_data, str) and img_data.startswith("["):
            url = img_data.replace('[', '').replace(']', '').replace('"', '').replace("'", "").split(',')[0].strip()
        else:
            url = str(img_data)
        
        # 2. Upgrade to HTTPS
        url = url.replace("http://", "https://")

        # 3. Request the image pretending to be a browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        
        # 4. Return the image object directly
        return Image.open(BytesIO(response.content))
    except: 
        return "https://via.placeholder.com/150"

def get_smart_recommendations(user_input, max_items=6):
    query = auto_clean(user_input)
    cat_mask = df['brand'].str.lower().str.contains(query, na=False)
    name_mask = df['product_name'].str.lower().str.contains(query, na=False)
    combined = df[cat_mask | name_mask].copy()

    if combined.empty:
        all_names = df['product_name'].tolist()
        match = process.extractOne(query, all_names, scorer=fuzz.token_set_ratio)
        if match and match[1] > 70:
            combined = df[df['product_name'] == match[0]].copy()
        else: return None

    combined['relevance_score'] = 0
    combined.loc[combined['brand'].str.lower().str.contains(query, na=False), 'relevance_score'] += 10
    acc_words = ['cable', 'glass', 'cover', 'case', 'usb', 'mount', 'adapter']
    is_acc = combined['product_name'].str.lower().str.contains('|'.join(acc_words), na=False)
    combined.loc[~is_acc, 'relevance_score'] += 5
    
    return combined.sort_values(by=['relevance_score', 'retail_price'], ascending=[False, False]).head(max_items)

# --- 3. STREAMLIT UI ---
st.set_page_config(layout="wide")
st.title("🛒 Smart Recommendation Engine")
st.caption('By Mr.jamal')

with st.form("search_form"):
    user_query = st.text_input("What are you looking for?", placeholder="Search here...")
    submit_button = st.form_submit_button("Search Now", type='primary')

if submit_button and user_query:
    results = get_smart_recommendations(user_query)
    
    if results is not None:
        cols = st.columns(4) 
        for i, (idx, row) in enumerate(results.iterrows()):
            with cols[i % 4]:
                # This now returns a PIL Image object, which Streamlit handles better
                img_to_show = get_image_url(row['image'])
                
                st.image(img_to_show, use_container_width=True)
                st.caption(f"**{row['product_name'][:30]}...**")
                st.markdown(f"**₹{row['retail_price']}**")
    else:
        st.warning("No products found.")
