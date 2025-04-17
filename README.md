# DataCleaningApp: Advanced Data Processing Tool

[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/frankysoo/DataCleaningApp)
[![Status](https://img.shields.io/badge/Status-Active-green.svg)](https://github.com/frankysoo/DataCleaningApp)

A powerful and intuitive Flask web application I've developed for uploading, merging, and cleaning CSV/Excel files using advanced Pandas techniques. This application offers intelligent data preprocessing with a beautiful, user-friendly interface and robust backend processing capabilities, capable of handling files up to 400MB in size.

## 📋 Table of Contents

- [Features](#-features)
- [Installation and Setup](#-installation-and-setup)
- [Technical Stack](#-technical-stack)
- [Usage Guide](#-usage-guide)
- [Sample Files](#-sample-files)
- [API Documentation](#-api-documentation)
- [Data Cleaning Logic](#-data-cleaning-logic)
- [Error Handling](#-error-handling)
- [Future Enhancements](#-future-enhancements)

## ✨ Features

- **Large File Support:** Process files up to 400MB with optimized chunked processing
- **Upload & Process:** Upload one or more CSV or Excel files and process them in a single operation
- **Smart File Detection:** Automatically detects file encodings, delimiters, and formats with intelligent handling of complex cases
- **Intelligent Cleaning:** Comprehensive configurable cleaning options including:
  - Remove null/empty rows
  - Remove duplicate entries
  - Standardize text formatting
  - Fill missing values intelligently
  - Fix date formats automatically
  - Trim whitespace from text
  - Standardize phone numbers
  - Validate and fix email addresses
  - Standardize boolean values (yes/no, true/false)
  - Extract numeric values from currency strings
  - Normalize text (remove accents, special characters)
- **Memory-Efficient Processing:** Optimized algorithms for handling large datasets without memory issues
- **Interactive Visualizations:** Preview original and cleaned data with dynamic charts and statistics
- **Multi-file Support:** Seamlessly merge multiple files with intelligent column mapping
- **Error Handling:** Robust error handling with detailed logging and graceful fallbacks
- **Download Options:** Download the cleaned data as Excel or CSV with one click

## 🔧 Installation and Setup

### Prerequisites

Before setting up the project, make sure your system has the following installed:

- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Step-by-Step Setup Instructions

1. **Clone the repository**

   Clone the repository to your local machine and navigate to the project directory:
   ```
   git clone https://github.com/frankysoo/DataCleaningApp.git
   cd DataCleaningApp
   ```

2. **Create a virtual environment**

   Create and activate a virtual environment to isolate the project dependencies.

   For Windows:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   For macOS/Linux:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   Install the required Python packages:

   ```
   pip install flask flask-sqlalchemy pandas numpy openpyxl chardet email-validator
   ```

   For production environments, you may also want to install:
   ```
   pip install gunicorn psycopg2-binary
   ```

4. **Create necessary directories**

   Create the following directories in the project root:
   ```
   mkdir -p uploads output sample_files
   ```

### Database Configuration

1. **SQLite Database (Default)**

   By default, the application uses SQLite, which requires no additional setup. The database file `app.db` will be created automatically in the project root directory.

2. **PostgreSQL Database (Optional)**

   If you prefer to use PostgreSQL:
   - Create a new PostgreSQL database and user with appropriate permissions
   - Set the `DATABASE_URL` environment variable to your PostgreSQL connection string
     Format: `postgresql://username:password@localhost/database_name`

3. **Set environment variables (Optional)**

   You can customize the application by setting these environment variables:

   - `DATABASE_URL`: The connection string for your database (defaults to SQLite if not set)
   - `SESSION_SECRET`: A secure random key for session encryption (defaults to a development key if not set)

4. **Initialize the database**

   The application will automatically create the necessary tables when first run.

### Running the Application

1. **Generate sample files (optional)**

   Run the sample file generator to create test data:
   ```
   python create_sample_files.py
   ```

2. **Start the application**

   For development:
   ```
   python main.py
   ```

   For production with gunicorn (Linux/macOS):
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

3. **Access the application**

   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

### Troubleshooting

- **Database connection issues**: If using PostgreSQL, verify that your PostgreSQL service is running.
- **Missing dependencies**: Ensure all required packages are installed.
- **Permission issues**: Ensure the application has read/write access to the uploads, output, and sample_files directories.
- **Database issues**: If you encounter database problems, you can delete the app.db file (if using SQLite) and restart the application to create a fresh database.

## 🚀 Technical Stack

- **Backend:** Python, Flask, Pandas, SQLAlchemy, NumPy
- **Frontend:** HTML5, CSS3, JavaScript with Bootstrap 5 for responsive UI
- **Data Processing:** Pandas, NumPy, Openpyxl for Excel handling
- **Database:** SQLite (default) or PostgreSQL for storing cleaning history and statistics
- **Visualization:** Chart.js for interactive data visualizations
- **Styling:** Custom CSS with Bootstrap dark theme integration

## 📊 Usage Guide

1. **Access the application** through the browser at `http://localhost:5000`
2. **Upload files**:
   - Click the "Choose CSV or Excel files" button
   - Select one or more files (.csv, .xlsx, .xls) from your computer
   - Alternatively, try one of the sample files in the "Try with Sample Data" section
3. **Configure cleaning options**:
   - Toggle standard cleaning options like removing duplicates and filling nulls
   - Enable advanced options for phone/email standardization and text normalization
4. **Process the files**:
   - Click "Upload and Clean" button to start processing
   - Wait for the processing to complete (this may take a few moments depending on file size)
5. **View results**:
   - Browse the "Original Data" and "Cleaned Data" tabs to compare before and after
   - Check the "Cleaning Statistics" section for details on the changes made
6. **Download the cleaned data**:
   - Click the "Download Cleaned Data" button to get the processed file
7. **View cleaning history**:
   - Recent cleaning jobs are displayed at the bottom of the page
   - You can download previously cleaned files from this section

## 🧪 Sample Files

The application includes a variety of sample files to demonstrate its capabilities:
- **Employee Records (Excel):** Dataset with employee information, mixed phone formats, salary formatting issues, and inconsistent boolean values
- **Sales Data (Excel):** Dataset with sales transactions, currency formatting issues, multiple date formats, and inconsistent status values
- **Malformed Data (Excel):** Intentionally problematic data with mixed types, inconsistent dates, and duplicate rows to test cleaning capabilities
- **Sample Products (Excel):** Product catalog with inconsistent categories and missing stock information
- **Employee Data (CSV):** CSV version of employee data with formatting inconsistencies
- **Sales Data (CSV):** CSV version of sales transactions with multiple formatting issues

## 🔌 API Documentation

The application provides a simple but powerful API:

- `POST /upload`: Upload and process files with customizable cleaning options
- `GET /use-sample/<filename>`: Process a pre-loaded sample file with cleaning options
- `GET /download/<filename>`: Download a processed file
- `GET /jobs`: List all previous cleaning jobs

## 🧹 Data Cleaning Logic

The application applies intelligent cleaning based on detected data types:

1. **For date-like columns:**
   - Converts various date formats to standardized datetime
   - Handles international date notations (MM/DD/YYYY, DD/MM/YYYY, etc.)
   - Repairs partial or malformed dates when possible

2. **For numeric columns:**
   - Converts text-based numbers to true numeric types
   - Handles currency symbols and regional formatting (€, $, etc.)
   - Extracts numeric values from mixed text strings
   - Fills missing values intelligently based on column context

3. **For text columns:**
   - Standardizes case and removes excess whitespace
   - Normalizes text with accent removal (optional)
   - Handles categorical data with smart standardization
   - Standardizes phone numbers and email addresses

4. **For boolean columns:**
   - Detects and standardizes various boolean representations
   - Handles yes/no, true/false, 0/1, and other formats

## 🛡️ Error Handling

The application includes comprehensive error handling for:
- Invalid file formats
- Encoding issues and non-standard character sets
- Data type conversion failures
- Merging problems with mismatched columns
- Database connectivity issues
- Processing timeouts and memory limitations

## 🔮 Future Enhancements

I'm actively working on the following improvements:
- Custom cleaning rules definition per column
- Advanced data transformation pipelines
- Additional visualization options and interactive dashboards
- Export to more formats (JSON, Parquet, etc.)
- API key authentication for programmatic access
- Machine learning-based data cleaning suggestions
- Cloud storage integration for even larger files
- Collaborative cleaning with multi-user support

## 👨‍💻 About the Developer

I've been developing this tool over the past two years as part of my data science journey. The application has evolved from a simple CSV cleaner to a comprehensive data processing platform capable of handling large and complex datasets.

Feel free to reach out with any questions or suggestions for improvement!

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

Thanks to all the open-source libraries that made this project possible:

- Flask: Web framework
- Pandas: Data processing
- Bootstrap: UI components
- Chart.js: Data visualization
- NumPy: Numerical computing
- SQLAlchemy: Database ORM

