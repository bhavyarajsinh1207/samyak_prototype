# pages/analysis_kpis.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
from utils.excel_functions import apply_excel_function
from utils.helpers import px_with_template


def show_page():
    st.header("📈 Step 4: Analysis & KPIs")
    st.info("Create key performance indicators and analyze your data.")

    # --- Ensure session defaults ---
    if "clean_df" not in st.session_state or st.session_state.clean_df is None:
        st.warning("No data loaded. Please go back to Step 1: Data Import.")
        return

    if "kpis" not in st.session_state:
        st.session_state.kpis = []

    if "processing_steps" not in st.session_state:
        st.session_state.processing_steps = []

    df = st.session_state.clean_df

    if df.empty:
        st.warning("Dataset is empty. Please check your data import step.")
        return

    # --- Data Overview ---
    st.subheader("📋 Data Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", f"{df.shape[0]:,}")
    with col2:
        st.metric("Columns", f"{df.shape[1]:,}")
    with col3:
        st.metric("Numeric Columns", len(df.select_dtypes(include=np.number).columns))
    with col4:
        st.metric(
            "Categorical Columns", len(df.select_dtypes(exclude=np.number).columns)
        )

    # --- Missing Values Analysis ---
    miss = df.isna().sum().sort_values(ascending=False)
    if miss.sum() > 0:
        st.subheader("⚠️ Missing Values Summary")
        st.dataframe(
            miss[miss > 0].to_frame("Missing Count").style.format("{:,}"),
            use_container_width=True,
        )
    else:
        st.info("🎉 No missing values detected!")

    st.markdown("---")

    # --- KPI Creation ---
    st.subheader("🎯 Create Custom KPIs")
    st.markdown(
        "Define your Key Performance Indicators using column aggregations or Excel-like expressions."
    )

    kpi_col1, kpi_col2, kpi_col3 = st.columns([2, 2, 1])

    with kpi_col1:
        kpi_name = st.text_input(
            "KPI Name", placeholder="e.g., Total Revenue, Unique Customers"
        )
        kpi_column = st.selectbox(
            "Select Column", options=["(none)"] + list(df.columns)
        )

    with kpi_col2:
        kpi_func = st.selectbox(
            "Calculation Method",
            [
                "(manual)",
                "sum",
                "mean",
                "median",
                "min",
                "max",
                "count",
                "nunique",
                "excel_expr",
            ],
        )
        kpi_value = ""
        kpi_expr = ""
        if kpi_func == "(manual)":
            kpi_value = st.text_input(
                "Manual Value", placeholder='e.g., 12345.67 or "High Performance"'
            )
        elif kpi_func == "excel_expr":
            kpi_expr = st.text_input(
                "Excel Expression", placeholder="=SUM(Sales) or =AVERAGE(Price)"
            )

    with kpi_col3:
        st.write("")
        st.write("")
        if st.button("➕ Add KPI", type="primary"):
            try:
                value = None
                kpi_type = "number"

                if not kpi_name:
                    st.error("Please enter a KPI Name.")
                elif kpi_func == "(manual)":
                    value = kpi_value
                    kpi_type = "text"
                elif kpi_func == "excel_expr":
                    expr = kpi_expr.strip()
                    if not expr.startswith("="):
                        expr = "=" + expr
                    value = apply_excel_function(expr, df)
                    kpi_type = "number"
                elif kpi_column != "(none)":
                    if kpi_func == "sum":
                        value = df[kpi_column].sum()
                    elif kpi_func == "mean":
                        value = df[kpi_column].mean()
                    elif kpi_func == "median":
                        value = df[kpi_column].median()
                    elif kpi_func == "min":
                        value = df[kpi_column].min()
                    elif kpi_func == "max":
                        value = df[kpi_column].max()
                    elif kpi_func == "count":
                        value = df[kpi_column].count()
                    elif kpi_func == "nunique":
                        value = df[kpi_column].nunique()
                    kpi_type = "number"

                if value is not None:
                    st.session_state.kpis.append(
                        {"name": kpi_name, "value": value, "type": kpi_type}
                    )
                    st.success(f"✅ KPI '{kpi_name}' added!")
                    st.session_state.processing_steps.append(
                        f"Added KPI: {kpi_name} = {value}"
                    )
                else:
                    st.error("Could not calculate KPI value.")
            except Exception as e:
                st.error(f"❌ Error creating KPI: {str(e)}")

    # --- Display KPIs ---
    if st.session_state.kpis:
        st.subheader("📊 Your KPIs")
        cols = st.columns(min(4, len(st.session_state.kpis)))
        for i, kpi in enumerate(st.session_state.kpis):
            with cols[i % len(cols)]:
                if kpi["type"] == "number":
                    try:
                        st.metric(kpi["name"], f"{float(kpi['value']):,.2f}")
                    except Exception:
                        st.metric(kpi["name"], str(kpi["value"]))
                else:
                    st.metric(kpi["name"], str(kpi["value"]))

    st.markdown("---")

    # --- Statistical Summary ---
    st.subheader("📊 Statistical Summary")
    numeric_cols = df.select_dtypes(include=np.number).columns
    if len(numeric_cols) > 0:
        stats_df = df[numeric_cols].describe().T
        stats_df["median"] = df[numeric_cols].median()
        stats_df["variance"] = df[numeric_cols].var()
        stats_df["skewness"] = df[numeric_cols].apply(lambda x: stats.skew(x.dropna()))
        stats_df["kurtosis"] = df[numeric_cols].apply(
            lambda x: stats.kurtosis(x.dropna())
        )
        st.dataframe(stats_df.style.format("{:,.2f}"), use_container_width=True)
    else:
        st.info("No numeric columns for statistical summary.")

    # --- Correlation Matrix ---
    if len(numeric_cols) > 1:
        st.subheader("🔗 Correlation Matrix")
        corr_matrix = df[numeric_cols].corr()
        try:
            fig = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix",
            )
            fig = px_with_template(fig, st.session_state.theme)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)

    st.markdown("---")

    # --- Categorical Analysis ---
    cat_cols = df.select_dtypes(exclude=np.number).columns
    if len(cat_cols) > 0:
        st.subheader("📊 Categorical Analysis")
        selected_cat_col = st.selectbox("Select categorical column", options=cat_cols)
        if selected_cat_col:
            value_counts = df[selected_cat_col].value_counts().reset_index()
            value_counts.columns = [selected_cat_col, "Count"]
            value_counts["Percentage"] = (
                value_counts["Count"] / value_counts["Count"].sum() * 100
            ).round(2)
            st.dataframe(
                value_counts.style.format({"Count": "{:,}", "Percentage": "{:.1f}%"}),
                use_container_width=True,
            )

    st.markdown("---")

    # --- Navigation to Step 5 ---

    if st.button("➡️ Proceed to Visualization", type="primary"):
        st.query_params["step"] = 5
        st.rerun()
