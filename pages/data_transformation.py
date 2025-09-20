# pages/data_transformation.py
import streamlit as st
import pandas as pd
import numpy as np
from utils.excel_functions import apply_excel_function
from utils.helpers import fetch_exchange_rates

def show_page():
    st.header("🔄 Step 3: Data Transformation")
    st.info("Transform your data with calculated columns, type casting, and feature engineering.")

    if st.session_state.clean_df.empty:
        st.warning("No data loaded. Please go back to Step 1: Data Import.")
        return

    df = st.session_state.clean_df

    # Use tabs for different transformation types
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Calculated Columns", "🎯 Type Casting", "📅 Date Features", "🔍 Find & Replace", "💱 Currency Converter", "🔗 Merge Columns"])

    with tab1:
        st.subheader("Create Calculated Columns")
        st.markdown("""
        **Examples:**
        - `price * quantity` (Python expression)
        - `=SUM(column1, column2)` (Excel function)
        - `=IF(sales > 1000, "High", "Low")` (Excel conditional)
        """)

        calc_col = st.text_input('New column name', placeholder='e.g., Total_Revenue', help="Enter the name for your new calculated column.")
        calc_expr = st.text_area('Expression', height=100,
                                placeholder='Enter calculation formula',
                                help="Use Python expressions or Excel functions starting with =")

        if st.button('➕ Add Calculated Column', type="primary"):
            if not calc_expr:
                st.warning('Please enter an expression.')
            else:
                try:
                    if calc_expr.strip().startswith('=') or '(' in calc_expr:
                        res = apply_excel_function(calc_expr, df)
                        col_name = calc_col if calc_col else "calculated_column"
                        st.session_state.clean_df[col_name] = res
                        st.success(f"✅ Added column '{col_name}' using Excel function.")
                        st.session_state.processing_steps.append(f"Added calculated column: {col_name} = {calc_expr}")
                    else:
                        local_vars = {col: df[col] for col in df.columns}
                        local_vars.update({'np': np, 'pd': pd})
                        value = pd.eval(calc_expr, engine='python', local_dict=local_vars)
                        col_name = calc_col if calc_col else calc_expr.replace(" ", "_")
                        st.session_state.clean_df[col_name] = value
                        st.success(f"✅ Added column '{col_name}' using expression.")
                        st.session_state.processing_steps.append(f"Added calculated column: {col_name} = {calc_expr}")
                except Exception as e:
                    st.error(f'❌ Calculation failed: {str(e)}')

    with tab2:
        st.subheader("Change Column Types")
        tcol = st.selectbox('Select column to convert', options=list(df.columns), help="Choose the column whose data type you want to change.")
        ttype = st.selectbox('Convert to', ['int','float','str','category','bool','datetime'], help="Select the target data type.")

        if st.button('🔄 Apply Type Conversion', type="primary"):
            if tcol:
                try:
                    if ttype == 'int':
                        st.session_state.clean_df[tcol] = pd.to_numeric(df[tcol], errors='coerce').astype('Int64')
                    elif ttype == 'float':
                        st.session_state.clean_df[tcol] = pd.to_numeric(df[tcol], errors='coerce').astype(float)
                    elif ttype == 'str':
                        st.session_state.clean_df[tcol] = df[tcol].astype(str)
                    elif ttype == 'category':
                        st.session_state.clean_df[tcol] = df[tcol].astype('category')
                    elif ttype == 'bool':
                        st.session_state.clean_df[tcol] = df[tcol].apply(lambda x: bool(x) if pd.notna(x) else False)
                    elif ttype == 'datetime':
                        st.session_state.clean_df[tcol] = pd.to_datetime(df[tcol], errors='coerce')
                    st.success(f"✅ Converted '{tcol}' to {ttype}.")
                    st.session_state.processing_steps.append(f"Converted column '{tcol}' to {ttype}")
                except Exception as e:
                    st.error(f'❌ Conversion failed: {str(e)}')

    with tab3:
        st.subheader("Extract Date Components")
        date_cols_options = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.to_datetime(df[col], errors='coerce').notna().any()]
        date_col = st.selectbox('Select datetime column', options=['(none)'] + date_cols_options, help="Choose a column to extract date parts from.")

        if st.button('⚙️ Extract Date Parts', type="primary"):
            if date_col != '(none)':
                try:
                    st.session_state.clean_df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    if st.session_state.clean_df[date_col].isnull().all():
                        st.error(f"❌ Column '{date_col}' cannot be converted to datetime.")
                    else:
                        st.session_state.clean_df[f'{date_col}_year'] = st.session_state.clean_df[date_col].dt.year.astype('Int64', errors='ignore')
                        st.session_state.clean_df[f'{date_col}_month'] = st.session_state.clean_df[date_col].dt.month.astype('Int64', errors='ignore')
                        st.session_state.clean_df[f'{date_col}_day'] = st.session_state.clean_df[date_col].dt.day.astype('Int64', errors='ignore')
                        st.session_state.clean_df[f'{date_col}_weekday'] = st.session_state.clean_df[date_col].dt.day_name()
                        st.success(f"✅ Extracted date components from '{date_col}'.")
                        st.session_state.processing_steps.append(f"Extracted date components from '{date_col}'")
                except Exception as e:
                    st.error(f'❌ Date extraction failed: {str(e)}')

    with tab4:
        st.subheader("Find and Replace Values")
        replace_col = st.selectbox('Column to modify', options=list(df.columns), help="Select the column where you want to find and replace values.")
        old_val = st.text_input('Value to find (leave empty for NA values)', help="Enter the value you want to replace.")
        new_val = st.text_input('Replacement value', help="Enter the value to replace the found values with.")

        if st.button('✏️ Apply Replacement', type="primary"):
            if replace_col:
                try:
                    if old_val == '':
                        replacement = np.nan if new_val == '' else new_val
                        st.session_state.clean_df[replace_col] = df[replace_col].fillna(replacement)
                        st.success(f"✅ Filled NA values in '{replace_col}' with '{replacement}'.")
                        st.session_state.processing_steps.append(f"Filled NA values in '{replace_col}' with '{replacement}'")
                    else:
                        try:
                            old_num = float(old_val)
                            st.session_state.clean_df[replace_col] = df[replace_col].replace(old_num, new_val)
                        except ValueError:
                            st.session_state.clean_df[replace_col] = df[replace_col].replace(old_val, new_val)
                        st.success(f"✅ Replaced '{old_val}' with '{new_val}' in '{replace_col}'.")
                        st.session_state.processing_steps.append(f"Replaced '{old_val}' with '{new_val}' in '{replace_col}'")
                except Exception as e:
                    st.error(f'❌ Replacement failed: {str(e)}')

    with tab5:
        st.subheader("Convert Currency Column")
        st.info("Converts a numeric column from one currency to another using live exchange rates.")

        numeric_cols = list(df.select_dtypes(include=np.number).columns)
        currency_col = st.selectbox('Select Numeric Column for Conversion',
                                    options=['(none)'] + numeric_cols,
                                    help="Choose the numeric column containing currency values to convert.")

        if currency_col != '(none)':
            all_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'INR']
            from_currency = st.selectbox('From Currency', options=all_currencies, index=0)
            to_currency = st.selectbox('To Currency', options=all_currencies, index=1)
            new_currency_col_name = st.text_input('New Column Name', value=f"{currency_col}_{to_currency}")

            if st.button('💱 Apply Currency Conversion', type="primary"):
                if from_currency == to_currency:
                    st.warning("Source and target currencies are the same.")
                else:
                    with st.spinner(f"Fetching exchange rates..."):
                        rates = fetch_exchange_rates(from_currency)
                        if rates and to_currency in rates:
                            exchange_rate = rates[to_currency]
                            try:
                                converted_series = pd.to_numeric(df[currency_col], errors='coerce') * exchange_rate
                                col_name = new_currency_col_name if new_currency_col_name else f"{currency_col}_converted_to_{to_currency}"
                                st.session_state.clean_df[col_name] = converted_series
                                st.success(f"✅ Successfully converted '{currency_col}' from {from_currency} to {to_currency} (Rate: {exchange_rate:.4f}).")
                                st.session_state.processing_steps.append(f"Converted '{currency_col}' from {from_currency} to {to_currency}")
                            except Exception as e:
                                st.error(f"❌ Error during conversion: {e}")
                        else:
                            st.error(f"❌ Could not fetch exchange rate from {from_currency} to {to_currency}.")

    with tab6:
        st.subheader("Merge Multiple Columns")
        st.markdown("Combine values from selected columns into a new column using a specified separator.")

        cols_to_merge = st.multiselect(
            'Select columns to merge',
            options=list(df.columns),
            help="Choose two or more columns whose values you want to combine."
        )
        merge_separator = st.text_input('Separator', value=' ')
        merged_col_name = st.text_input('New merged column name', placeholder='e.g., Full_Address')

        if st.button('➕ Merge Columns', type="primary"):
            if len(cols_to_merge) < 2:
                st.error("Please select at least two columns to merge.")
            elif not merged_col_name:
                st.error("Please enter a name for the new merged column.")
            else:
                try:
                    merged_series = df[cols_to_merge[0]].astype(str).fillna('')
                    for col in cols_to_merge[1:]:
                        merged_series = merged_series + merge_separator + df[col].astype(str).fillna('')
                    st.session_state.clean_df[merged_col_name] = merged_series
                    st.success(f"✅ Merged columns {', '.join(cols_to_merge)} into '{merged_col_name}'.")
                    st.session_state.processing_steps.append(f"Merged columns {', '.join(cols_to_merge)} into '{merged_col_name}'")
                except Exception as e:
                    st.error(f"❌ Failed to merge columns: {e}")

    st.markdown("---")
    
    # Show current data state
    st.subheader("📊 Transformed Data Preview")
    st.dataframe(st.session_state.clean_df.head(8), use_container_width=True)
    st.caption(f"Current shape: {st.session_state.clean_df.shape[0]:,} rows × {st.session_state.clean_df.shape[1]:,} columns")

# Navigation to Step 4
    if st.button('➡️ Proceed to Analysis', type="primary"):
        st.query_params["step"] = 4
        st.rerun()