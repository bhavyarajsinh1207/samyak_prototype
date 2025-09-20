# MultipleFiles/pages/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import math
import numpy as np

# Import for consistent Plotly theming
from utils.helpers import px_with_template


def show_page():
    st.header("📊 Step 7: Quick Dashboard")
    st.info("Assemble your key visualizations and KPIs into a custom dashboard.")

    # --- Ensure session defaults ---
    if "clean_df" not in st.session_state or st.session_state.clean_df is None:
        st.warning("No data loaded. Please go back to Step 1: Data Import.")
        return

    if "dashboard_chart_definitions" not in st.session_state:
        st.session_state.dashboard_chart_definitions = []

    if "kpis" not in st.session_state:
        st.session_state.kpis = []

    df = st.session_state.clean_df

    if df.empty:
        st.warning("Your dataset is empty. Please check the data import step.")
        return

    # --- KPIs ---
    st.subheader("🎯 Key Performance Indicators")
    if st.session_state.kpis:
        kpi_cols = st.columns(min(4, len(st.session_state.kpis)))
        for i, kpi in enumerate(st.session_state.kpis):
            with kpi_cols[i % len(kpi_cols)]:
                kpi_value_display = ""
                if kpi["type"] == "number":
                    try:
                        kpi_value_display = f"{float(kpi['value']):,.2f}"
                    except (ValueError, TypeError):
                        kpi_value_display = str(kpi["value"])
                else:
                    kpi_value_display = str(kpi["value"])

                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <h3>{kpi['name']}</h3>
                        <p>{kpi_value_display}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info(
            "No KPIs have been created yet. Go to 'Analysis & KPIs' to create some."
        )

    st.markdown("---")

    # --- Filters ---
    st.subheader("⚙️ Dashboard Filters")
    st.write("Apply filters to dynamically update all charts on the dashboard.")

    filter_options = {}
    categorical_cols_for_filter = df.select_dtypes(exclude=np.number).columns.tolist()
    if categorical_cols_for_filter:
        filter_col1, filter_col2 = st.columns(2)
        for i, col in enumerate(categorical_cols_for_filter):
            with filter_col1 if i % 2 == 0 else filter_col2:
                unique_vals = ["All"] + sorted(df[col].dropna().unique().tolist())
                selected_val = st.selectbox(
                    f"Filter by {col}",
                    options=unique_vals,
                    key=f"dashboard_filter_{col}",
                )
                if selected_val != "All":
                    filter_options[col] = selected_val
    else:
        st.info("No categorical columns available for filtering.")

    filtered_df = df.copy()
    for col, val in filter_options.items():
        filtered_df = filtered_df[filtered_df[col] == val]

    if filtered_df.empty:
        st.warning(
            "No data matches the selected filters. Please adjust your selections."
        )
    else:
        st.success(
            f"Displaying data for {filtered_df.shape[0]:,} rows after filtering."
        )

    st.markdown("---")

    # --- Auto Dashboard Generator ---
    st.subheader("🤖 Auto Dashboard Generator")
    if st.button("⚡ Generate Auto Dashboard", type="primary"):
        st.session_state.dashboard_chart_definitions.clear()
        auto_charts = _generate_auto_dashboard(filtered_df)
        st.session_state.dashboard_chart_definitions.extend(auto_charts)
        st.success(f"✅ Auto Dashboard created with {len(auto_charts)} charts!")

    st.markdown("---")

    # --- Custom Chart Creator ---
    st.subheader("📈 Add Custom Charts to Dashboard")

    chart_options = ["(none)"] + list(df.columns)
    col_chart_select, col_chart_type = st.columns(2)

    with col_chart_select:
        selected_x = st.selectbox(
            "Select X-axis", options=chart_options, key="dashboard_x_select"
        )
        selected_y = st.selectbox(
            "Select Y-axis", options=chart_options, key="dashboard_y_select"
        )

    with col_chart_type:
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Bar Chart", "Scatter Plot", "Histogram", "Box Plot", "Violin Plot"],
            key="dashboard_chart_type",
        )
        chart_title = st.text_input(
            "Chart Title (optional)", key="dashboard_chart_title"
        )

    if st.button("➕ Add Chart to Dashboard", type="primary"):
        if selected_x != "(none)":
            chart_def = {
                "type": chart_type,
                "x": selected_x,
                "y": None if selected_y == "(none)" else selected_y,
                "title": chart_title if chart_title else f"{chart_type}: {selected_x}",
            }
            st.session_state.dashboard_chart_definitions.append(chart_def)
            st.success("✅ Chart added to dashboard!")
        else:
            st.warning("Please select at least an X-axis column.")

    st.markdown("---")

    # --- Dashboard Layout ---
    if st.session_state.dashboard_chart_definitions:
        _render_dashboard_charts(filtered_df)
    else:
        st.info("No charts added yet. Use Auto Dashboard or create manually.")

    st.markdown("---")
    st.caption("Quick Dashboard | Enhanced Auto Data Analysis & Dashboard")


# 🔹 Auto Dashboard Generator
def _generate_auto_dashboard(df: pd.DataFrame):
    auto_charts = []
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # 1. Distribution for numeric columns
    for col in numeric_cols[:2]:
        auto_charts.append(
            {
                "type": "Histogram",
                "x": col,
                "y": None,
                "title": f"Distribution of {col}",
            }
        )

    # 2. Top categories
    for col in cat_cols[:2]:
        auto_charts.append(
            {
                "type": "Bar Chart",
                "x": col,
                "y": None,
                "title": f"Top Categories of {col}",
            }
        )

    # 3. Scatter plot if multiple numeric cols
    if len(numeric_cols) >= 2:
        auto_charts.append(
            {
                "type": "Scatter Plot",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
            }
        )

    return auto_charts


# 🔹 Chart Renderer
def _render_dashboard_charts(df_to_use: pd.DataFrame):
    st.subheader("📊 Dashboard Layout")
    charts_per_row = st.session_state.get("charts_per_row", 2)
    num_charts = len(st.session_state.dashboard_chart_definitions)
    num_rows = math.ceil(num_charts / charts_per_row)

    if df_to_use.empty:
        st.warning("Cannot render charts: Filtered data is empty.")
        return

    for i in range(num_rows):
        cols = st.columns(charts_per_row)
        for j in range(charts_per_row):
            idx = i * charts_per_row + j
            if idx < num_charts:
                chart_def = st.session_state.dashboard_chart_definitions[idx]
                fig = None
                try:
                    if chart_def["type"] == "Bar Chart":
                        fig = px.bar(
                            df_to_use,
                            x=chart_def["x"],
                            color=chart_def["x"],
                            title=chart_def["title"],
                        )
                    elif chart_def["type"] == "Scatter Plot" and chart_def["y"]:
                        fig = px.scatter(
                            df_to_use,
                            x=chart_def["x"],
                            y=chart_def["y"],
                            color=chart_def["x"],
                            title=chart_def["title"],
                        )
                    elif chart_def["type"] == "Histogram":
                        fig = px.histogram(
                            df_to_use,
                            x=chart_def["x"],
                            color=chart_def["x"],
                            title=chart_def["title"],
                        )
                    elif chart_def["type"] == "Box Plot" and chart_def["y"]:
                        fig = px.box(
                            df_to_use,
                            x=chart_def["x"],
                            y=chart_def["y"],
                            color=chart_def["x"],
                            title=chart_def["title"],
                        )
                    elif chart_def["type"] == "Violin Plot" and chart_def["y"]:
                        fig = px.violin(
                            df_to_use,
                            x=chart_def["x"],
                            y=chart_def["y"],
                            color=chart_def["x"],
                            box=True,
                            points="all",
                            title=chart_def["title"],
                        )

                    if fig:
                        fig = px_with_template(fig, st.session_state.theme)
                        with cols[j]:
                            st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    with cols[j]:
                        st.error(
                            f"Error rendering chart '{chart_def.get('title', chart_def['type'])}': {e}"
                        )

    st.markdown("---")
    if st.button("🗑️ Clear All Dashboard Charts", key="clear_dashboard_charts"):
        st.session_state.dashboard_chart_definitions = []
        st.rerun()

    # Navigation
    if st.button("➡️ Proceed to Reporting", type="primary"):
        st.query_params["step"] = 7
        st.rerun()
