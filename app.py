# app.py (optimized)
import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add the current directory to the path so we can import pages
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all pages
from pages import (
    data_import,
    data_cleaning,
    data_transformation,
    analysis_kpis,
    visualization,
    dashboard,
    reporting,
    ai_model,
    realtime_analysis,
)

# Import helper for theme and other utilities
from utils.helpers import apply_theme_css

st.set_page_config(
    page_title="Enhanced Auto Data Analysis", layout="wide", page_icon="📊"
)

# Initialize session state variables
defaults = {
    "theme": "Light",
    "kpis": [],
    "datasets": [],
    "current_step": 1,
    "df_raw": pd.DataFrame(),
    "clean_df": pd.DataFrame(),
    "dashboard_charts": [],
    "dashboard_chart_definitions": [],
    "processing_steps": [],
    "trained_model": None,
    "start_realtime": False,
    "db_config": None,
    "gdrive_files": {},
    "label_encoder": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Apply custom CSS for theming and responsive design
apply_theme_css(st.session_state.theme)

# --- Custom CSS for Responsiveness ---
st.markdown(
    """
<style>
/* Navbar Styling */
.navbar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,.1);
}
.navbar a {
    color: #007bff;
    text-decoration: none;
    margin: 5px;
    padding: 8px 12px;
    border-radius: 6px;
    transition: background-color 0.3s ease, color 0.3s ease;
    font-weight: 600;
    font-size: 0.95rem;
}
.navbar a:hover {
    background-color: #e2e6ea;
}
.navbar a.active {
    background-color: #007bff;
    color: white;
}
/* Dark Mode Navbar */
.stApp.dark-theme .navbar {
    background-color: #1E212B;
}
.stApp.dark-theme .navbar a {
    color: #8AB4F8;
}
.stApp.dark-theme .navbar a:hover {
    background-color: #3A3F4C;
}
.stApp.dark-theme .navbar a.active {
    background-color: #8AB4F8;
    color: #1E212B;
}

/* Responsive Fix for Sidebar */
[data-testid="stSidebar"] {
    width: 250px !important;
}
@media (max-width: 900px) {
    .navbar {
        flex-direction: column;
        align-items: stretch;
    }
    .navbar a {
        text-align: center;
        font-size: 0.9rem;
        padding: 10px;
    }
    [data-testid="stSidebar"] {
        width: 100% !important;
        position: relative;
    }
}

/* KPI Card Styling */
.kpi-card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,.1);
    text-align: center;
}
.kpi-card h3 {
    margin: 0;
    font-size: 0.9rem;
    color: #6c757d;
}
.kpi-card p {
    margin: 10px 0 0;
    font-size: 1.5rem;
    font-weight: bold;
    color: #007bff;
}

/* Dark theme adjustments */
.stApp.dark-theme .kpi-card {
    background-color: #2D3748;
}
.stApp.dark-theme .kpi-card h3 {
    color: #CBD5E0;
}
.stApp.dark-theme .kpi-card p {
    color: #63B3ED;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- Main App Header ---
st.title("📊 Enhanced Auto Data Analysis & Dashboard")
st.caption(
    "Workflow: 1. Import → 2. Clean → 3. Transform → 4. Analyze → 5. Visualize → 6. Dashboard → 7. Report → 8. AI Model → 9. Real-time"
)

# --- Navbar Logic ---
query_params = st.query_params
current_step_from_url = int(query_params.get("step", st.session_state.current_step))
st.session_state.current_step = current_step_from_url

step_options = {
    "1. Data Import": 1,
    "2. Data Cleaning": 2,
    "3. Data Transformation": 3,
    "4. Analysis & KPIs": 4,
    "5. Visualization": 5,
    "6. Quick Dashboard": 6,
    "7. Reporting": 7,
    "8. AI Model Training": 8,
    "9. Real-time Analysis": 9,
}
active_classes = {
    f"active_step_{step_num}": (
        "active" if st.session_state.current_step == step_num else ""
    )
    for step_num in step_options.values()
}

# Render Navbar
navbar_html = "<div class='navbar'>"
for step_name, step_num in step_options.items():
    navbar_html += f"<a href='?step={step_num}' target='_self' class='{active_classes[f'active_step_{step_num}']}'>{step_name}</a>"
navbar_html += "</div>"
st.markdown(navbar_html, unsafe_allow_html=True)

# --- Sidebar (Settings + Progress) ---
with st.sidebar:
    st.markdown(
        "<h3 style='text-align:center;'>⚙️ Settings</h3>", unsafe_allow_html=True
    )

    st.session_state.theme = st.radio(
        "Theme",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1,
        horizontal=True,
    )

    st.session_state.charts_per_row = st.number_input(
        "Charts per row (Dashboard)", min_value=1, max_value=4, value=2
    )

    st.markdown("---")
    st.header("📋 Workflow Progress")

    for step_name, step_num in step_options.items():
        if st.button(
            f"{'✅' if st.session_state.current_step > step_num else '📌'} {step_name}",
            use_container_width=True,
            type=(
                "primary" if st.session_state.current_step == step_num else "secondary"
            ),
        ):
            st.session_state.current_step = step_num
            st.query_params["step"] = step_num
            st.rerun()

# Progress bar
progress = st.session_state.current_step / len(step_options)
st.progress(
    progress, text=f"Step {st.session_state.current_step} of {len(step_options)}"
)

# --- Main Content Area ---
pages = {
    1: data_import.show_page,
    2: data_cleaning.show_page,
    3: data_transformation.show_page,
    4: analysis_kpis.show_page,
    5: visualization.show_page,
    6: dashboard.show_page,
    7: reporting.show_page,
    8: ai_model.show_page,
    9: realtime_analysis.show_page,
}

try:
    pages[st.session_state.current_step]()
except Exception as e:
    st.error(f"Error loading page: {e}")
    st.info("Try navigating to another step or refreshing.")

st.markdown("---")
st.caption("Enhanced Auto Data Analysis & Dashboard | Built with Streamlit")
