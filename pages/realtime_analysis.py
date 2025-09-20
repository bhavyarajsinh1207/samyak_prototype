# pages/realtime_analysis.py
import streamlit as st
import pandas as pd
import time
import plotly.express as px
from utils.db_connector import (
    get_db_connection,
    fetch_data_from_db,
)  # Assuming these functions
from utils.helpers import px_with_template


def show_page():
    st.header("⚡ Step 9: Real-time Analysis")
    st.info("Connect to a database and visualize data that updates periodically.")

    # --- Database Connection Configuration ---
    st.subheader("🔗 Database Connection")
    db_type = st.selectbox(
        "Database Type", ["PostgreSQL", "MySQL", "SQL Server", "SQLite (file)"]
    )
    db_host = st.text_input("Host", "localhost")
    db_port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
    db_name = st.text_input("Database Name", "your_database")
    db_user = st.text_input("Username", "your_user")
    db_password = st.text_input(
        "Password", type="password", value="your_password"
    )  # Use st.secrets for production!
    db_table = st.text_input("Table Name", "your_table")
    refresh_interval = st.slider(
        "Refresh Interval (seconds)", min_value=5, max_value=60, value=10
    )

    # --- Connect and Fetch Data ---
    connect_button = st.button("Connect & Start Real-time Analysis", type="primary")

    if connect_button:
        st.session_state.db_config = {
            "type": db_type,
            "host": db_host,
            "port": db_port,
            "name": db_name,
            "user": db_user,
            "password": db_password,
            "table": db_table,
        }
        st.session_state.start_realtime = True
        st.success("Attempting to connect to database...")
        st.session_state.processing_steps.append(
            f"Attempted real-time connection to {db_type} table: {db_table}"
        )

    if st.session_state.get("start_realtime", False):
        st.subheader("📊 Live Data & Metrics")

        # Placeholder for live data and charts
        data_placeholder = st.empty()
        metrics_placeholder = st.empty()
        chart_placeholder = st.empty()

        while st.session_state.get("start_realtime", False):
            try:
                if conn := get_db_connection(st.session_state.db_config):
                    live_df = fetch_data_from_db(
                        conn, st.session_state.db_config["table"]
                    )
                    conn.close()

                    if not live_df.empty:
                        with data_placeholder.container():
                            st.write(
                                f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                            st.dataframe(live_df.head(5), use_container_width=True)
                            st.caption(f"Total rows: {live_df.shape[0]}")

                        with metrics_placeholder.container():
                            st.markdown("---")
                            st.subheader("Key Metrics")
                            col1, col2, col3 = st.columns(3)
                            numeric_cols = live_df.select_dtypes(
                                include=np.number
                            ).columns
                            if len(numeric_cols) > 0:
                                col1.metric(
                                    "Avg. Value (first numeric)",
                                    f"{live_df[numeric_cols[0]].mean():,.2f}",
                                )
                                if len(numeric_cols) > 1:
                                    col2.metric(
                                        "Sum Value (second numeric)",
                                        f"{live_df[numeric_cols[1]].sum():,.0f}",
                                    )
                                else:
                                    col2.metric(
                                        "Unique Values", f"{live_df.nunique().sum():,}"
                                    )
                            col3.metric(
                                "New Rows (since last refresh)",
                                f"{live_df.shape[0] - st.session_state.clean_df.shape[0] if not st.session_state.clean_df.empty else live_df.shape[0]:,}",
                            )
                            st.session_state.clean_df = (
                                live_df.copy()
                            )  # Update clean_df with live data

                        with chart_placeholder.container():
                            st.markdown("---")
                            st.subheader("Live Chart")
                            if len(numeric_cols) > 0:
                                # Example: Histogram of the first numeric column
                                fig = px.histogram(
                                    live_df,
                                    x=numeric_cols[0],
                                    title=f"Live Distribution of {numeric_cols[0]}",
                                )
                                fig = px_with_template(fig, st.session_state.theme)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No numeric columns to plot live charts.")
                    else:
                        data_placeholder.warning(
                            "No data fetched from the database. Check table name or filters."
                        )
                else:
                    data_placeholder.error(
                        "Failed to connect to the database. Please check credentials and connection details."
                    )
                    st.session_state.start_realtime = (
                        False  # Stop trying if connection fails
                    )

            except Exception as e:
                data_placeholder.error(f"An error occurred during data fetch: {e}")
                st.session_state.start_realtime = False  # Stop trying on error

            time.sleep(refresh_interval)
            st.rerun()  # Rerun the app to update the display

    if st.session_state.get("start_realtime", False) and st.button(
        "Stop Real-time Analysis"
    ):
        st.session_state.start_realtime = False
        st.info("Real-time analysis stopped.")
        st.session_state.processing_steps.append("Stopped real-time analysis.")

    st.markdown("---")

    # Navigation
    if st.button("⬅️ Back to Data Import", type="secondary"):
        st.query_params["step"] = 1
        st.rerun()
