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
    df.drop(
        ['crawl_timestamp','product_url','overall_rating','is_FK_Advantage_product'],
        axis=1,
        inplace=True,
        errors='ignore'
    )
    df.drop_duplicates(inplace=True)
    df['brand'] = df['brand'].fillna('unknown')
    df['retail_price'] = df['retail_price'].fillna(df['retail_price'].median())
    df['image'] = df['image'].fillna('')
    df = df.drop_duplicates(subset=['product_name'], keep='first').reset_index(drop=True)
    return df

df = load_d_
