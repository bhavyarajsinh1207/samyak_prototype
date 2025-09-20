# pages/reporting.py
import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime
from utils.report_generators import generate_pdf_report, generate_docx_report
from utils.google_drive_utils import get_gdrive_service, upload_gdrive_file, list_gdrive_files # NEW

def show_page():
    st.header("📋 Step 7: Reporting")
    st.info("Generate professional reports in PDF or DOCX format with rich customization, insights, and appendix options.")

    if st.session_state.clean_df.empty:
        st.warning("⚠️ No data loaded. Please go back to Step 1: Data Import.")
        return

    df = st.session_state.clean_df

    # --- Report Configuration ---
    st.subheader("📝 Report Configuration")

    col1, col2 = st.columns(2)
    with col1:
        report_title = st.text_input("Report Title", "Data Analysis Report")
        report_author = st.text_input("Author", "Data Analyst")
        company_name = st.text_input("Company/Organization", "Your Company")
        company_logo = st.file_uploader("Upload Company Logo (optional)", type=["png", "jpg", "jpeg"])
    with col2:
        report_date = st.date_input("Report Date", datetime.now().date())
        custom_footer = st.text_input("Footer Text", "Confidential - For Internal Use Only")
        include_cover = st.checkbox("Include Cover Page", value=True)
        include_toc = st.checkbox("Include Table of Contents", value=True)

    # --- Content Selection ---
    st.subheader("📋 Content to Include")

    content_col1, content_col2 = st.columns(2)
    with content_col1:
        include_exec_summary = st.checkbox("Executive Summary", value=True)
        include_data_overview = st.checkbox("Data Overview", value=True)
        include_kpis = st.checkbox("Key Performance Indicators", value=True)
        include_statistics = st.checkbox("Statistical Summary", value=True)
        include_data_dict = st.checkbox("Data Dictionary", value=True)
    with content_col2:
        include_missing_analysis = st.checkbox("Missing Values Analysis", value=True)
        include_correlations = st.checkbox("Correlation Analysis", value=False)
        include_processing_steps = st.checkbox("Processing Steps", value=True)
        include_recommendations = st.checkbox("Recommendations", value=True)
        include_chart_gallery = st.checkbox("Chart Gallery", value=False)

    # --- Additional Custom Inputs ---
    st.subheader("🖊️ Custom Notes & Appendix")
    custom_notes = st.text_area("Add Custom Notes/Recommendations")
    appendix_file = st.file_uploader("Upload Appendix File (optional)", type=["pdf", "docx", "xlsx"])

    # --- Report Format Selection ---
    st.subheader("📄 Export Format")
    report_format = st.radio("Choose format", ["PDF", "DOCX", "Both (ZIP)"], horizontal=True)

    # --- Google Drive Upload Option ---
    st.subheader("☁️ Google Drive Upload")
    upload_to_gdrive = st.checkbox("Upload generated reports to Google Drive")
    gdrive_service = None
    gdrive_folder_options = {"My Drive Root": None} # Default option
    if upload_to_gdrive:
        gdrive_service = get_gdrive_service()
        if gdrive_service:
            st.success("Connected to Google Drive for upload.")
            try:
                # List folders for user to select
                gdrive_folders = list_gdrive_files(gdrive_service, folder_id=None) # List root folders
                for f in gdrive_folders:
                    if f['mimeType'] == 'application/vnd.google-apps.folder':
                        gdrive_folder_options[f['title']] = f['id']
                
                selected_gdrive_folder_name = st.selectbox(
                    "Select target Google Drive folder",
                    list(gdrive_folder_options.keys())
                )
                selected_gdrive_folder_id = gdrive_folder_options[selected_gdrive_folder_name]

            except Exception as e:
                st.error(f"Error listing Google Drive folders: {e}")
                gdrive_service = None # Disable upload if error
        else:
            st.warning("Google Drive service not available for upload. Please check authentication.")


    st.markdown("---")

    # --- Generate Report ---
    if st.button(f"🔄 Generate {report_format} Report", type="primary"):
        try:
            with st.spinner(f"Generating {report_format} report..."):
                # Prepare report data
                report_data = {
                    'title': report_title,
                    'author': report_author,
                    'company': company_name,
                    'logo': company_logo.read() if company_logo else None,
                    'footer': custom_footer,
                    'date': report_date.strftime("%B %d, %Y"),
                    'dataframe': df,
                    'kpis': st.session_state.kpis,
                    'processing_steps': st.session_state.processing_steps,
                    'custom_notes': custom_notes,
                    'appendix_file': appendix_file.read() if appendix_file else None,
                    # Flags
                    'include_cover': include_cover,
                    'include_toc': include_toc,
                    'include_exec_summary': include_exec_summary,
                    'include_data_overview': include_data_overview,
                    'include_kpis': include_kpis,
                    'include_statistics': include_statistics,
                    'include_data_dict': include_data_dict,
                    'include_missing_analysis': include_missing_analysis,
                    'include_correlations': include_correlations,
                    'include_processing_steps': include_processing_steps,
                    'include_recommendations': include_recommendations,
                    'include_chart_gallery': include_chart_gallery
                }

                files_to_download = []
                files_to_upload_gdrive = []

                # Generate Reports
                if report_format in ["PDF", "Both (ZIP)"]:
                    pdf_bytes = generate_pdf_report(report_data)
                    files_to_download.append(("pdf", "application/pdf", pdf_bytes))
                    files_to_upload_gdrive.append((pdf_bytes, f"{report_title.replace(' ', '_')}.pdf", "application/pdf"))

                if report_format in ["DOCX", "Both (ZIP)"]:
                    docx_bytes = generate_docx_report(report_data)
                    files_to_download.append((
                        "docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        docx_bytes
                    ))
                    files_to_upload_gdrive.append((docx_bytes, f"{report_title.replace(' ', '_')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))

                # Provide downloads
                if report_format == "Both (ZIP)":
                    import zipfile
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for ext, _, content in files_to_download:
                            zf.writestr(f"{report_title.replace(' ', '_')}.{ext}", content)
                    st.success("✅ PDF + DOCX Reports generated successfully!")
                    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
                    href = f'<a href="data:application/zip;base64,{b64}" download="{report_title.replace(" ", "_")}_Reports.zip">📥 Download ZIP</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    for ext, mime, content in files_to_download:
                        b64 = base64.b64encode(content).decode()
                        href = f'<a href="data:{mime};base64,{b64}" download="{report_title.replace(" ", "_")}.{ext}">📥 Download {ext.upper()} Report</a>'
                        st.markdown(href, unsafe_allow_html=True)

                # Upload to Google Drive
                if upload_to_gdrive and gdrive_service:
                    with st.spinner("Uploading reports to Google Drive..."):
                        for file_bytes, file_name, mime_type in files_to_upload_gdrive:
                            success = upload_gdrive_file(gdrive_service, file_bytes, file_name, mime_type, selected_gdrive_folder_id)
                            if success:
                                st.success(f"⬆️ Uploaded '{file_name}' to Google Drive.")
                                st.session_state.processing_steps.append(f"Uploaded '{file_name}' to Google Drive.")
                            else:
                                st.error(f"❌ Failed to upload '{file_name}' to Google Drive.")


                st.session_state.processing_steps.append(f"Generated {report_format} report: {report_title}")

        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")

    st.markdown("---")

    # --- Quick Preview ---
    st.subheader("👀 Quick Report Preview")
    if st.button("Generate Preview", type="secondary"):
        with st.expander("Report Preview", expanded=True):
            st.subheader(report_title)
            st.caption(f"Prepared by: {report_author} | {company_name} | {report_date.strftime('%B %d, %Y')}")

            if include_exec_summary:
                st.subheader("Executive Summary")
                st.info("This report highlights trends, anomalies, and insights extracted from the dataset.")

            if include_data_overview:
                st.subheader("Data Overview")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Rows", f"{df.shape[0]:,}")
                col2.metric("Total Columns", f"{df.shape[1]:,}")
                col3.metric("Numeric Columns", len(df.select_dtypes(include=np.number).columns))
                col4.metric("Categorical Columns", len(df.select_dtypes(exclude=np.number).columns))

            if include_data_dict:
                st.subheader("Data Dictionary")
                dict_df = pd.DataFrame({
                    "Column": df.columns,
                    "Data Type": df.dtypes.astype(str),
                    "Missing %": df.isnull().mean().round(2) * 100,
                    "Unique Values": df.nunique()
                })
                st.dataframe(dict_df)

            if include_kpis and st.session_state.kpis:
                st.subheader("Key Performance Indicators")
                kpi_cols = st.columns(min(3, len(st.session_state.kpis)))
                for i, kpi in enumerate(st.session_state.kpis):
                    with kpi_cols[i % len(kpi_cols)]:
                        st.metric(kpi['name'], str(kpi['value']))

            if include_processing_steps and st.session_state.processing_steps:
                st.subheader("Processing Steps")
                for i, step in enumerate(st.session_state.processing_steps, 1):
                    st.write(f"{i}. {step}")

            if custom_notes:
                st.subheader("Custom Notes")
                st.markdown(custom_notes)

    st.markdown("---")

    # Navigation
    if st.button('➡️ Proceed to AI Model Training', type="primary"): 
        st.query_params["step"] = 8 
        st.rerun()