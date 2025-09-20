#!/bin/bash

# Create the main project directory
mkdir -p data_don

# Create the pages directory and its files
mkdir -p data_don/pages
touch data_don/pages/data_import.py
touch data_don/pages/data_cleaning.py
touch data_don/pages/data_transformation.py
touch data_don/pages/analysis_kpis.py
touch data_don/pages/visualization.py
touch data_don/pages/reporting.py
touch data_don/pages/dashboard.py # Added dashboard.py

# Create the utils directory and its files
mkdir -p data_don/utils
touch data_don/utils/helpers.py
touch data_don/utils/excel_functions.py
touch data_don/utils/report_generators.py

# Create the main app file and requirements
touch data_don/app.py
touch data_don/requirements.txt

# Create a static directory for assets like logos
mkdir -p data_don/static
touch data_don/static/.gitkeep # Placeholder file

# Add some basic content to key files (optional, but good for initial setup)
echo "# Main application file" > data_don/app.py
echo "# Add your project dependencies here" > data_don/requirements.txt
echo "# Helper functions" > data_don/utils/helpers.py
echo "# Excel-related functions" > data_don/utils/excel_functions.py
echo "# Report generation utilities" > data_don/utils/report_generators.py

# Make the script executable (optional)
chmod +x "$0"

echo "Project structure created successfully!"
echo "Location: $(pwd)/data_don/"
