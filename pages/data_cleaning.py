# pages/data_cleaning.py
import streamlit as st
import pandas as pd
import numpy as np

def show_page():
    st.header("🧹 Step 2: Data Cleaning")
    st.info("Clean your dataset by handling missing values, duplicates, and outliers.")

    if st.session_state.clean_df.empty:
        st.warning("No data loaded. Please go back to Step 1: Data Import.")
        return

    df = st.session_state.clean_df.copy()

    # Create tabs for different cleaning operations
    tab1, tab2, tab3 = st.tabs(["🔧 Basic Cleaning", "🔄 Value Imputation", "📊 Outlier Handling"])

    with tab1:
        st.subheader("Basic Cleaning Operations")
        rm_dup = st.checkbox('Remove duplicate rows', value=True, help="Eliminate exact duplicate rows from the dataset.")
        drop_nulls = st.checkbox('Drop rows with any null values', value=False, help="Remove any row that contains at least one missing value.")
        drop_columns = st.multiselect('Select columns to remove', options=list(df.columns), help="Choose columns that are not needed for analysis and will be permanently removed.")

    with tab2:
        st.subheader("Value Imputation Options")
        impute_mode = st.selectbox(
            'Handle missing values:',
            ['No imputation', 'Numeric: Mean | Categorical: Mode', 'Fill with constant value'],
            help="Select a strategy to fill missing values. 'No imputation' leaves them as is."
        )
        fill_const = ''
        if impute_mode == 'Fill with constant value':
            fill_const = st.text_input('Constant value to fill with', value='0', help="Enter the value to replace all missing entries (e.g., 0, 'N/A').")

        fill_forward = st.checkbox('Fill forward/backward for remaining NAs', value=False, help="Apply forward-fill (ffill) then backward-fill (bfill).")

    with tab3:
        st.subheader("Outlier Handling Methods")
        clip_numeric = st.checkbox('Clip numeric outliers (auto-detect min/max)', value=False)
        use_zscore_outliers = st.checkbox('Handle outliers using Z-score', value=False)
        zscore_threshold = 3.0
        zscore_action = 'Clip'
        if use_zscore_outliers:
            zscore_threshold = st.slider('Z-score Threshold', min_value=1.0, max_value=5.0, value=3.0, step=0.1)
            zscore_action = st.radio('Z-score Outlier Action', ['Clip', 'Remove Row'], index=0)

    st.markdown("---")
    
    # Data quality metrics
    st.subheader("📈 Data Quality Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Missing Values", f"{df.isna().sum().sum():,}")
    with col2:
        st.metric("Total Duplicate Rows", f"{df.duplicated().sum():,}")
    with col3:
        st.metric("Current Rows", f"{df.shape[0]:,}")
    with col4:
        st.metric("Current Columns", f"{df.shape[1]:,}")

    st.markdown("---")
    
    if st.button('🔄 Apply Cleaning Operations', type="primary"):
        try:
            _df = df.copy()
            steps_taken = []

            # Drop selected columns
            if drop_columns:
                _df.drop(columns=drop_columns, inplace=True, errors='ignore')
                steps_taken.append(f"Removed columns: {', '.join(drop_columns)}")

            # Remove duplicate rows
            if rm_dup:
                initial_rows = _df.shape[0]
                _df.drop_duplicates(inplace=True)
                removed = initial_rows - _df.shape[0]
                if removed > 0:
                    steps_taken.append(f"Removed {removed} duplicate rows")

            # Drop rows with nulls
            if drop_nulls:
                initial_rows = _df.shape[0]
                _df.dropna(inplace=True)
                removed = initial_rows - _df.shape[0]
                if removed > 0:
                    steps_taken.append(f"Removed {removed} rows with null values")

            # Imputation
            if impute_mode == 'Numeric: Mean | Categorical: Mode':
                num_cols = _df.select_dtypes(include=np.number).columns
                cat_cols = _df.select_dtypes(exclude=np.number).columns

                for col in num_cols:
                    if _df[col].isnull().any():
                        _df[col].fillna(_df[col].mean(), inplace=True)
                steps_taken.append("Imputed numeric columns with mean values")

                for c in cat_cols:
                    if _df[c].isnull().any():
                        mode_val = _df[c].mode()
                        if not mode_val.empty:
                            _df[c].fillna(mode_val.iloc[0], inplace=True)
                steps_taken.append("Imputed categorical columns with mode values")

            elif impute_mode == 'Fill with constant value' and fill_const != '':
                _df.fillna(fill_const, inplace=True)
                steps_taken.append(f"Filled missing values with: '{fill_const}'")

            # Forward/backward fill
            if fill_forward:
                _df.fillna(method='ffill', inplace=True)
                _df.fillna(method='bfill', inplace=True)
                steps_taken.append("Applied forward/backward filling")

            # Clip numeric outliers
            if clip_numeric:
                for c in _df.select_dtypes(include=np.number).columns:
                    mn, mx = _df[c].min(), _df[c].max()
                    _df[c] = pd.to_numeric(_df[c], errors='coerce').clip(lower=mn, upper=mx)
                steps_taken.append("Clipped numeric outliers")

            # Z-score outlier handling
            if use_zscore_outliers:
                for c in _df.select_dtypes(include=np.number).columns:
                    series = pd.to_numeric(_df[c], errors='coerce').dropna()
                    if len(series) < 2:
                        continue
                    mean, std = series.mean(), series.std()
                    if std == 0:
                        continue
                    z_scores = (series - mean) / std
                    outlier_mask = (z_scores.abs() > zscore_threshold)
                    if zscore_action == 'Clip':
                        upper, lower = mean + zscore_threshold * std, mean - zscore_threshold * std
                        _df[c] = _df[c].clip(lower=lower, upper=upper)
                    elif zscore_action == 'Remove Row':
                        _df = _df.drop(series[outlier_mask].index)
                steps_taken.append(f"Handled outliers using Z-score ({zscore_action})")

            # Update session state
            st.session_state.clean_df = _df
            st.session_state.processing_steps.extend([f"Cleaning: {s}" for s in steps_taken])
            st.success("🎉 Cleaning applied successfully!")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Error during cleaning: {str(e)}")

    st.markdown("---")
    
    # Show results
    if 'df_raw' in st.session_state and not st.session_state.df_raw.empty:
        st.subheader("✅ Cleaning Results Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Original Rows", f"{st.session_state.df_raw.shape[0]:,}")
            st.metric("Original Columns", f"{st.session_state.df_raw.shape[1]:,}")
        with col2:
            st.metric("Cleaned Rows", f"{st.session_state.clean_df.shape[0]:,}")
            st.metric("Cleaned Columns", f"{st.session_state.clean_df.shape[1]:,}")

        st.subheader("Cleaned Data Preview")
        st.dataframe(st.session_state.clean_df.head(10), use_container_width=True)
        st.caption(f"Current shape: {st.session_state.clean_df.shape[0]:,} rows × {st.session_state.clean_df.shape[1]:,} columns")

        if st.button('➡️ Proceed to Transformation', type="primary"):
            st.query_params["step"] = 3
            st.rerun()
    else:
        st.info("No raw data available to show cleaning results. Please import data first.")
