# MultipleFiles/pages/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    
    # Enhanced chart types with all 8 types
    chart_types = [
        "Bar Chart",
        "Line Chart", 
        "Pie Chart",
        "Histogram",
        "Scatter Plot",
        "Area Chart",
        "Box Plot",
        "Violin Plot",
        "Heatmap"
    ]
    
    col_chart_select, col_chart_type, col_chart_options = st.columns(3)

    with col_chart_select:
        selected_x = st.selectbox(
            "Select X-axis/Category", options=chart_options, key="dashboard_x_select"
        )
        selected_y = st.selectbox(
            "Select Y-axis/Values", options=chart_options, key="dashboard_y_select"
        )
        selected_color = st.selectbox(
            "Color by (optional)", options=["None"] + list(df.columns), key="dashboard_color_select"
        )

    with col_chart_type:
        chart_type = st.selectbox(
            "Select Chart Type",
            chart_types,
            key="dashboard_chart_type",
        )
        chart_title = st.text_input(
            "Chart Title (optional)", key="dashboard_chart_title"
        )
        
    with col_chart_options:
        st.write("Chart Options")
        show_legend = st.checkbox("Show Legend", value=True, key="dashboard_show_legend")
        horizontal = st.checkbox("Horizontal Orientation", value=False, key="dashboard_horizontal") if chart_type == "Bar Chart" else False
        
        # Additional options for specific chart types
        if chart_type == "Pie Chart":
            hole_size = st.slider("Donut Hole Size", 0.0, 0.8, 0.0, 0.1, key="dashboard_hole_size")
        else:
            hole_size = 0.0

    if st.button("➕ Add Chart to Dashboard", type="primary"):
        if selected_x != "(none)" or chart_type in ["Histogram", "Heatmap"]:
            chart_def = {
                "type": chart_type,
                "x": None if selected_x == "(none)" else selected_x,
                "y": None if selected_y == "(none)" else selected_y,
                "color": None if selected_color == "None" else selected_color,
                "title": chart_title if chart_title else f"{chart_type}: {selected_x if selected_x != '(none)' else 'Data'}",
                "options": {
                    "show_legend": show_legend,
                    "horizontal": horizontal,
                    "hole_size": hole_size
                }
            }
            st.session_state.dashboard_chart_definitions.append(chart_def)
            st.success("✅ Chart added to dashboard!")
        else:
            st.warning("Please select at least an X-axis column or use a chart type that doesn't require it.")

    st.markdown("---")

    # --- Dashboard Layout ---
    if st.session_state.dashboard_chart_definitions:
        _render_dashboard_charts(filtered_df)
        
        # Chart Management Section
        st.subheader("🔄 Manage Charts")
        col1, col2, col3 = st.columns(3)
        with col1:
            charts_per_row = st.number_input("Charts per row", min_value=1, max_value=4, value=2, key="charts_per_row")
        with col2:
            if st.button("🗑️ Clear All Dashboard Charts", key="clear_dashboard_charts"):
                st.session_state.dashboard_chart_definitions = []
                st.rerun()
        with col3:
            if st.button("🔄 Remove Last Chart", key="remove_last_chart"):
                if st.session_state.dashboard_chart_definitions:
                    st.session_state.dashboard_chart_definitions.pop()
                    st.rerun()
        
        # Individual chart removal
        st.write("Remove specific charts:")
        chart_to_remove = st.selectbox(
            "Select chart to remove",
            options=range(len(st.session_state.dashboard_chart_definitions)),
            format_func=lambda i: f"{i+1}. {st.session_state.dashboard_chart_definitions[i]['title']}"
        )
        if st.button("🗑️ Remove Selected Chart"):
            st.session_state.dashboard_chart_definitions.pop(chart_to_remove)
            st.rerun()
    else:
        st.info("No charts added yet. Use Auto Dashboard or create manually.")

    st.markdown("---")
    st.caption("Quick Dashboard | Enhanced Auto Data Analysis & Dashboard")


# 🔹 Auto Dashboard Generator
def _generate_auto_dashboard(df: pd.DataFrame):
    auto_charts = []
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # 1. Distribution for first numeric column
    if numeric_cols:
        auto_charts.append(
            {
                "type": "Histogram",
                "x": numeric_cols[0],
                "y": None,
                "color": None,
                "title": f"Distribution of {numeric_cols[0]}",
                "options": {"show_legend": True, "horizontal": False, "hole_size": 0.0}
            }
        )

    # 2. Bar chart for first categorical column
    if cat_cols:
        auto_charts.append(
            {
                "type": "Bar Chart",
                "x": cat_cols[0],
                "y": None,
                "color": None,
                "title": f"Top Categories of {cat_cols[0]}",
                "options": {"show_legend": True, "horizontal": False, "hole_size": 0.0}
            }
        )

    # 3. Line chart if date column exists (try to find date-like column)
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if date_cols and numeric_cols:
        auto_charts.append(
            {
                "type": "Line Chart",
                "x": date_cols[0],
                "y": numeric_cols[0],
                "color": None,
                "title": f"{numeric_cols[0]} over {date_cols[0]}",
                "options": {"show_legend": True, "horizontal": False, "hole_size": 0.0}
            }
        )
    elif len(numeric_cols) >= 2:
        # Scatter plot if multiple numeric cols and no date
        auto_charts.append(
            {
                "type": "Scatter Plot",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "color": cat_cols[0] if cat_cols else None,
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
                "options": {"show_legend": True, "horizontal": False, "hole_size": 0.0}
            }
        )

    # 4. Pie chart for second categorical column
    if len(cat_cols) >= 2:
        auto_charts.append(
            {
                "type": "Pie Chart",
                "x": cat_cols[1],
                "y": numeric_cols[0] if numeric_cols else None,
                "color": None,
                "title": f"Distribution of {cat_cols[1]}",
                "options": {"show_legend": True, "horizontal": False, "hole_size": 0.0}
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
                    # Get chart parameters
                    x_col = chart_def.get('x')
                    y_col = chart_def.get('y')
                    color_col = chart_def.get('color')
                    options = chart_def.get('options', {})
                    
                    # Handle different chart types
                    if chart_def["type"] == "Bar Chart":
                        if x_col:
                            if options.get('horizontal', False):
                                fig = px.bar(
                                    df_to_use,
                                    y=x_col,
                                    color=color_col if color_col else x_col,
                                    title=chart_def["title"],
                                    orientation='h'
                                )
                            else:
                                fig = px.bar(
                                    df_to_use,
                                    x=x_col,
                                    color=color_col if color_col else x_col,
                                    title=chart_def["title"],
                                )
                    
                    elif chart_def["type"] == "Line Chart":
                        if x_col and y_col:
                            fig = px.line(
                                df_to_use,
                                x=x_col,
                                y=y_col,
                                color=color_col,
                                title=chart_def["title"],
                                markers=True
                            )
                    
                    elif chart_def["type"] == "Pie Chart":
                        if x_col:
                            if y_col:
                                # Aggregate data for pie chart
                                pie_data = df_to_use.groupby(x_col)[y_col].sum().reset_index()
                                fig = px.pie(
                                    pie_data,
                                    names=x_col,
                                    values=y_col,
                                    title=chart_def["title"],
                                    hole=options.get('hole_size', 0.0)
                                )
                            else:
                                # Count based on frequency
                                fig = px.pie(
                                    df_to_use,
                                    names=x_col,
                                    title=chart_def["title"],
                                    hole=options.get('hole_size', 0.0)
                                )
                    
                    elif chart_def["type"] == "Histogram":
                        if x_col:
                            fig = px.histogram(
                                df_to_use,
                                x=x_col,
                                color=color_col,
                                title=chart_def["title"],
                                marginal="box"
                            )
                    
                    elif chart_def["type"] == "Scatter Plot":
                        if x_col and y_col:
                            fig = px.scatter(
                                df_to_use,
                                x=x_col,
                                y=y_col,
                                color=color_col,
                                title=chart_def["title"],
                                trendline="ols" if df_to_use.shape[0] > 10 else None
                            )
                    
                    elif chart_def["type"] == "Area Chart":
                        if x_col and y_col:
                            fig = px.area(
                                df_to_use,
                                x=x_col,
                                y=y_col,
                                color=color_col,
                                title=chart_def["title"],
                                line_group=color_col
                            )
                    
                    elif chart_def["type"] == "Box Plot":
                        if x_col and y_col:
                            fig = px.box(
                                df_to_use,
                                x=x_col,
                                y=y_col,
                                color=color_col,
                                title=chart_def["title"],
                                points="outliers"
                            )
                        elif x_col:
                            fig = px.box(
                                df_to_use,
                                y=x_col,
                                title=chart_def["title"],
                                points="outliers"
                            )
                    
                    elif chart_def["type"] == "Violin Plot":
                        if x_col and y_col:
                            fig = px.violin(
                                df_to_use,
                                x=x_col,
                                y=y_col,
                                color=color_col,
                                box=True,
                                points="all",
                                title=chart_def["title"],
                            )
                        elif x_col:
                            fig = px.violin(
                                df_to_use,
                                y=x_col,
                                box=True,
                                points="all",
                                title=chart_def["title"],
                            )
                    
                    elif chart_def["type"] == "Heatmap":
                        # Create correlation matrix for numeric columns
                        numeric_df = df_to_use.select_dtypes(include=np.number)
                        if len(numeric_df.columns) > 1:
                            corr_matrix = numeric_df.corr()
                            fig = px.imshow(
                                corr_matrix,
                                text_auto=True,
                                aspect="auto",
                                title=chart_def["title"],
                                color_continuous_scale='RdBu_r'
                            )
                    
                    # Apply template and display
                    if fig:
                        fig.update_layout(
                            showlegend=options.get('show_legend', True),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        fig = px_with_template(fig, st.session_state.theme)
                        with cols[j]:
                            st.plotly_chart(fig, use_container_width=True)
                            # Add remove button for individual chart
                            if st.button(f"❌ Remove", key=f"remove_chart_{idx}"):
                                st.session_state.dashboard_chart_definitions.pop(idx)
                                st.rerun()
                    else:
                        with cols[j]:
                            st.warning(f"Could not generate {chart_def['type']}. Check column selections.")

                except Exception as e:
                    with cols[j]:
                        st.error(
                            f"Error rendering chart '{chart_def.get('title', chart_def['type'])}': {str(e)}"
                        )

    # Navigation
    st.markdown("---")
    if st.button("➡️ Proceed to Reporting", type="primary"):
        st.query_params["step"] = 7
        st.rerun()
