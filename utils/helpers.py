# utils/helpers.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from datetime import datetime

def apply_theme_css(theme):
    """Apply CSS based on selected theme"""
    if theme == "Dark":
        st.markdown("""
        <style>
            .stApp {
                background-color: #1E212B;
                color: #FAFAFA;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp {
                background-color: #FFFFFF;
                color: #31333F;
            }
        </style>
        """, unsafe_allow_html=True)

def read_any_bytes(filename, content):
    """Read various file formats from bytes"""
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(BytesIO(content))
        elif filename.endswith(('.txt', '.tsv')):
            # Try to detect delimiter
            sample = content[:1000].decode('utf-8', errors='ignore')
            if '\t' in sample:
                return pd.read_csv(BytesIO(content), delimiter='\t')
            else:
                return pd.read_csv(BytesIO(content), delimiter=None, engine='python')
        else:
            raise ValueError(f"Unsupported file format: {filename}")
    except Exception as e:
        raise ValueError(f"Error reading file {filename}: {str(e)}")

def fetch_url(url):
    """Fetch data from a URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        filename = url.split('/')[-1] or f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return filename, response.content
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch URL {url}: {str(e)}")

def fetch_exchange_rates(base_currency):
    """Fetch live exchange rates from a free API"""
    try:
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{base_currency}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('rates', {})
    except:
        # Fallback to static rates if API fails
        rates = {
            'USD': {'EUR': 0.85, 'GBP': 0.73, 'JPY': 110.5, 'CAD': 1.25, 'AUD': 1.35},
            'EUR': {'USD': 1.18, 'GBP': 0.86, 'JPY': 130.0, 'CAD': 1.47, 'AUD': 1.59},
            'GBP': {'USD': 1.37, 'EUR': 1.16, 'JPY': 151.0, 'CAD': 1.70, 'AUD': 1.84},
        }
        return rates.get(base_currency, {})

def px_with_template(fig, theme):
    """Apply consistent styling to Plotly figures"""
    if theme == "Dark":
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0)'
        )
    else:
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
    return fig