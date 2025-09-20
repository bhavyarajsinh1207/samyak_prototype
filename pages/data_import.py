# pages/data_import.py
import streamlit as st
import pandas as pd
from utils.helpers import read_any_bytes, fetch_url
from utils.google_drive_utils import get_gdrive_service, list_gdrive_files, download_gdrive_file
from utils.db_connector import get_db_connection, fetch_data_from_db

def show_page():
    st.header("📥 Step 1: Data Import")
    st.info("Upload your data files or fetch them from URLs. Supported formats: CSV, Excel (xlsx, xls), TXT, TSV.")

    # Initialize session state if not exists
    if "datasets" not in st.session_state:
        st.session_state.datasets = []
    if "processing_steps" not in st.session_state:
        st.session_state.processing_steps = []

    # --- Tabs for different import methods ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 File Upload",
        "🌐 URL Import",
        "☁️ Google Drive",
        "🗄️ Database"
    ])

    # ---------------- TAB 1: File Upload ----------------
    with tab1:
        uploaded_files = st.file_uploader(
            "Upload CSV/Excel files",
            type=["csv", "xlsx", "xls", "txt", "tsv"],
            accept_multiple_files=True,
            help="Drag and drop your data files here. Multiple files can be uploaded."
        )

        if uploaded_files:
            for f in uploaded_files:
                try:
                    content = f.read()
                    df = read_any_bytes(f.name, content)
                    st.session_state.datasets.append((f.name, df))
                    st.success(f"✅ Loaded {f.name} with shape {df.shape}")
                    st.session_state.processing_steps.append(
                        f"Imported file: {f.name} with {df.shape[0]} rows and {df.shape[1]} columns"
                    )
                except Exception as e:
                    st.error(f"❌ Failed to load {f.name}: {str(e)}")

    # ---------------- TAB 2: URL Import ----------------
    with tab2:
        st.subheader("🌐 Fetch Data from URL")
        url_input = st.text_area(
            "Enter URLs (one per line) to fetch CSV/XLSX files",
            placeholder="e.g.,\nhttps://example.com/data.csv\nhttps://another.site/spreadsheet.xlsx"
        )

        if st.button("Fetch URLs", type="secondary"):
            urls = [u.strip() for u in url_input.splitlines() if u.strip()]
            if not urls:
                st.warning("Please enter at least one URL.")
            else:
                for url in urls:
                    try:
                        fname, content = fetch_url(url)
                        df = read_any_bytes(fname, content)
                        st.session_state.datasets.append((fname, df))
                        st.success(f"✅ Loaded {fname} from URL with shape {df.shape}")
                        st.session_state.processing_steps.append(
                            f"Imported from URL: {url} with {df.shape[0]} rows and {df.shape[1]} columns"
                        )
                    except Exception as e:
                        st.error(f"❌ Failed to fetch {url}: {str(e)}")

    # ---------------- TAB 3: Google Drive ----------------
    with tab3:
        st.subheader("☁️ Import from Google Drive")
        if st.button("Connect to Google Drive"):
            gdrive_service = get_gdrive_service()
            if gdrive_service:
                st.session_state.gdrive_service = gdrive_service
                st.success("Connected to Google Drive.")
            else:
                st.error("Failed to connect to Google Drive.")

        if hasattr(st.session_state, 'gdrive_service') and st.session_state.gdrive_service:
            folder_id = st.text_input(
                "Enter Google Drive Folder ID (optional, leave empty for My Drive root)", ""
            )

            if st.button("List Files in Google Drive"):
                try:
                    file_list = list_gdrive_files(
                        st.session_state.gdrive_service,
                        folder_id if folder_id else None
                    )
                    if file_list:
                        st.session_state.gdrive_files = {
                            f['title']: f['id']
                            for f in file_list
                            if f['mimeType'] != 'application/vnd.google-apps.folder'
                        }
                        st.info(f"Found {len(st.session_state.gdrive_files)} files.")
                    else:
                        st.warning("No files found in the specified folder or My Drive root.")
                        st.session_state.gdrive_files = {}
                except Exception as e:
                    st.error(f"Error listing Google Drive files: {str(e)}")
                    st.session_state.gdrive_files = {}

            if st.session_state.get('gdrive_files'):
                selected_file = st.selectbox(
                    "Select a file to import",
                    list(st.session_state.gdrive_files.keys())
                )
                if selected_file and st.button(f"Import '{selected_file}' from Google Drive"):
                    file_id = st.session_state.gdrive_files[selected_file]
                    with st.spinner(f"Downloading '{selected_file}'..."):
                        try:
                            content_bytes, actual_file_name = download_gdrive_file(
                                st.session_state.gdrive_service,
                                file_id,
                                selected_file
                            )
                            df = read_any_bytes(actual_file_name, content_bytes)
                            st.session_state.datasets.append((actual_file_name, df))
                            st.success(f"✅ Loaded {actual_file_name} with shape {df.shape}")
                            st.session_state.processing_steps.append(
                                f"Imported from Google Drive: {actual_file_name} with {df.shape[0]} rows and {df.shape[1]} columns"
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to import {selected_file}: {str(e)}")

    # ---------------- TAB 4: Database Import ----------------
    with tab4:
        st.subheader("🗄️ Import from Database")
        db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQL Server", "SQLite"])
        db_host = st.text_input("Host", "localhost")
        db_port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
        db_name = st.text_input("Database Name", "your_database")
        db_user = st.text_input("Username", "your_user")
        db_password = st.text_input("Password", type="password", value="")
        db_table = st.text_input("Table Name", "your_table")
        query_limit = st.number_input("Query Limit (rows)", min_value=1, value=1000)

        if st.button("Connect & Import from Database", type="primary"):
            db_config = {
                "type": db_type,
                "host": db_host,
                "port": db_port,
                "name": db_name,
                "user": db_user,
                "password": db_password,
                "table": db_table
            }
            with st.spinner(f"Connecting to {db_type} and fetching data from '{db_table}'..."):
                try:
                    conn = get_db_connection(db_config)
                    if conn:
                        df = fetch_data_from_db(conn, db_table, query_limit)
                        conn.close()
                        if not df.empty:
                            dataset_name = f"DB_{db_table}"
                            st.session_state.datasets.append((dataset_name, df))
                            st.success(f"✅ Loaded {df.shape[0]} rows from database table '{db_table}'.")
                            st.session_state.processing_steps.append(
                                f"Imported from DB table: {db_table} with {df.shape[0]} rows and {df.shape[1]} columns"
                            )
                        else:
                            st.warning(f"No data fetched from table '{db_table}'.")
                    else:
                        st.error("Failed to establish database connection.")
                except Exception as e:
                    st.error(f"❌ Error importing from database: {str(e)}")

    # ---------------- Final Section: Dataset Selection ----------------
    st.markdown("---")

    if st.session_state.datasets:
        st.subheader("📊 Loaded Datasets")

        # Show dataset previews
        for i, (name, df) in enumerate(st.session_state.datasets):
            with st.expander(f"Dataset {i+1}: {name} ({df.shape[0]} rows × {df.shape[1]} columns)"):
                st.dataframe(df.head(), use_container_width=True)

        # Choose single dataset or combine
        combine_mode = st.radio(
            "How to use the datasets?",
            ["Single dataset", "Combine all datasets"],
            index=0
        )

        df_raw = pd.DataFrame()

        if combine_mode == "Single dataset":
            names = [n for n, _ in st.session_state.datasets]
            selected = st.selectbox("Select dataset to use", names)
            if selected:
                df_raw = next(df for n, df in st.session_state.datasets if n == selected)
        else:
            add_source = st.checkbox(
                "Add 'source' column when combining",
                value=True
            )
            dfs = []
            for n, df in st.session_state.datasets:
                df_temp = df.copy()
                if add_source:
                    df_temp["source"] = n
                dfs.append(df_temp)
            try:
                df_raw = pd.concat(dfs, ignore_index=True)
                st.success(f"✅ Combined {len(dfs)} datasets. Total shape: {df_raw.shape}")
                st.session_state.processing_steps.append(
                    f"Combined {len(dfs)} datasets → {df_raw.shape[0]} rows × {df_raw.shape[1]} cols"
                )
            except Exception as e:
                st.error(f"❌ Error combining datasets: {str(e)}")
                return

        # Save to session
        st.session_state.df_raw = df_raw
        st.session_state.clean_df = df_raw.copy()

        if not df_raw.empty:
            st.subheader("Preview of Data for Analysis")
            st.dataframe(df_raw.head(10), use_container_width=True)
            st.caption(f"Shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]:,} columns")

            if st.button("➡️ Proceed to Cleaning", type="primary"):
                st.query_params["step"] = 2
                st.rerun()
    else:
        st.info("Upload files, fetch from URL, Google Drive, or DB to continue.")