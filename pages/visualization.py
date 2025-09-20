# pages/visualization.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import px_with_template

# --- Utility: Display charts in grid layout ---
def display_charts_in_grid(figures, cols_per_row=3):
    """
    Display Plotly charts in a grid layout.
    :param figures: list of plotly figures
    :param cols_per_row: number of columns per row (3 = 3 charts per row)
    """
    if not figures:
        return
    for i in range(0, len(figures), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, fig in enumerate(figures[i:i+cols_per_row]):
            with cols[j]:
                st.plotly_chart(fig, use_container_width=True)


def show_page():
    st.header("📊 Step 5: Visualization")
    st.info("Create insightful visualizations from your data.")

    # --- Check if data is available ---
    if st.session_state.clean_df.empty:
        st.warning("⚠️ No data loaded. Please go back to Step 1: Data Import.")
        return

    df = st.session_state.clean_df

    # Let user pick grid layout (2 or 3 per row)
    grid_cols = st.radio(
        "Choose grid layout for charts:",
        options=[2, 3],
        index=1,
        horizontal=True
    )

    # -------------------------------------------------------------------
    # QUICK VISUALIZATIONS
    # -------------------------------------------------------------------
    st.subheader("🚀 Quick Visualizations")
    st.caption("Generate common visualizations with one click.")

    quick_charts = []

    # Numeric Distribution
    if st.button("📊 Numeric Distribution", use_container_width=True):
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) > 0:
            selected_col = st.selectbox("Select numeric column", numeric_cols, key="quick_num")
            if selected_col:
                fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}")
                fig = px_with_template(fig, st.session_state.theme)
                quick_charts.append(fig)

    # Top Categories
    if st.button("📈 Top Categories", use_container_width=True):
        cat_cols = df.select_dtypes(exclude='number').columns
        if len(cat_cols) > 0:
            selected_col = st.selectbox("Select categorical column", cat_cols, key="quick_cat")
            if selected_col:
                top_cats = df[selected_col].value_counts().head(10)
                fig = px.bar(x=top_cats.index, y=top_cats.values, title=f"Top 10 {selected_col} Categories")
                fig = px_with_template(fig, st.session_state.theme)
                quick_charts.append(fig)

    # Correlation Heatmap
    if st.button("🔗 Correlation Matrix", use_container_width=True):
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            fig = px.imshow(
                corr_matrix,
                text_auto='.2f',
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title="Correlation Matrix"
            )
            fig = px_with_template(fig, st.session_state.theme)
            quick_charts.append(fig)

    # Display quick visualizations
    if quick_charts:
        st.subheader("📊 Quick Visualization Results")
        display_charts_in_grid(quick_charts, cols_per_row=grid_cols)

    st.markdown("---")

    # -------------------------------------------------------------------
    # AUTO VISUALIZATION
    # -------------------------------------------------------------------
    st.subheader("🤖 Auto Visualization")
    st.caption("Automatically generate insights based on your dataset.")

    generate_all = st.checkbox(
        "Generate ALL possible visualizations (may be heavy on large datasets)",
        value=False
    )

    if not generate_all:
        max_num_cols = st.slider(
            "How many numeric columns to visualize?",
            1,
            min(5, len(df.select_dtypes(include='number').columns)),
            3
        )
        max_cat_cols = st.slider(
            "How many categorical columns to visualize?",
            1,
            min(5, len(df.select_dtypes(exclude='number').columns)),
            2
        )
    else:
        max_num_cols = len(df.select_dtypes(include='number').columns)
        max_cat_cols = len(df.select_dtypes(exclude='number').columns)

    if st.button("🚀 Generate Auto Visualizations", type="primary", use_container_width=True):
        try:
            auto_charts = []
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            cat_cols = df.select_dtypes(exclude='number').columns.tolist()

            # 1. Numeric Distributions
            for col in numeric_cols[:max_num_cols]:
                fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                fig = px_with_template(fig, st.session_state.theme)
                auto_charts.append(fig)

            # 2. Top Categories
            for col in cat_cols[:max_cat_cols]:
                top_cats = df[col].value_counts().head(10)
                fig = px.bar(x=top_cats.index, y=top_cats.values, title=f"Top 10 {col} Categories")
                fig = px_with_template(fig, st.session_state.theme)
                auto_charts.append(fig)

            # 3. Correlation Heatmap
            if len(numeric_cols) >= 2:
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(
                    corr_matrix,
                    text_auto='.2f',
                    aspect="auto",
                    color_continuous_scale='RdBu_r',
                    title="Correlation Matrix"
                )
                fig = px_with_template(fig, st.session_state.theme)
                auto_charts.append(fig)

            # 4. Scatter Plots for numeric pairs
            if len(numeric_cols) >= 2:
                scatter_pairs = [
                    (numeric_cols[i], numeric_cols[j])
                    for i in range(len(numeric_cols))
                    for j in range(i+1, len(numeric_cols))
                ]
                for x, y in scatter_pairs[: (5 if not generate_all else len(scatter_pairs))]:
                    fig = px.scatter(df, x=x, y=y, title=f"{x} vs {y}")
                    fig = px_with_template(fig, st.session_state.theme)
                    auto_charts.append(fig)

            # Display auto visualizations in grid
            if auto_charts:
                st.subheader("📊 Auto Visualization Results")
                display_charts_in_grid(auto_charts, cols_per_row=grid_cols)

            # Save charts for dashboard
            for fig in auto_charts:
                chart_def = {
                    'type': 'Auto Chart',
                    'title': fig.layout.title.text,
                    'x_axis': '(auto)',
                    'y_axis': '(auto)',
                    'color_by': '(auto)',
                    'agg_func': 'None',
                    'fig': fig
                }
                st.session_state.dashboard_chart_definitions.append(chart_def)
                

            st.success("✅ Auto visualizations created and displayed in grid layout!")
            
        except Exception as e:
            st.error(f"❌ Error generating auto visualizations: {str(e)}")

    # Navigation to Step 6
    if st.button('➡️ Proceed to Dashboard', type="primary"):
        st.query_params["step"] = 6
        st.rerun()