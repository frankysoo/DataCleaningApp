import os
import logging
import shutil
import json
from datetime import datetime
import pandas as pd
import numpy as np
import math
from flask import Blueprint, request, send_from_directory, jsonify, render_template, current_app
from flask.json.provider import DefaultJSONProvider
from werkzeug.utils import secure_filename
import data_loader
import cleaner
from db import db
from models import CleaningJob

# Function to safely convert pandas DataFrames to JSON-safe dictionaries
def pandas_to_json_safe(df, orient='records'):
    """
    Convert pandas DataFrame to JSON-safe dictionary with proper handling of NaN, None, etc.

    Args:
        df: DataFrame to convert
        orient: Orientation format for conversion ('records', 'list', etc.)

    Returns:
        List or Dict that is safe for JSON serialization
    """
    if df is None or df.empty:
        return []

    # Make a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Create a dictionary to hold the result
    if orient == 'records':
        result = []
        for _, row in df_copy.iterrows():
            row_dict = {}
            for col in df_copy.columns:
                val = row[col]
                if pd.isna(val):
                    row_dict[col] = None
                elif isinstance(val, pd.Timestamp):
                    row_dict[col] = val.isoformat()
                elif isinstance(val, (np.integer, np.int64, np.int32)):
                    row_dict[col] = int(val)
                elif isinstance(val, (np.floating, float)):
                    if math.isnan(val) or math.isinf(val):
                        row_dict[col] = None
                    else:
                        row_dict[col] = float(val)
                elif isinstance(val, np.ndarray):
                    row_dict[col] = val.tolist()
                else:
                    row_dict[col] = val
            result.append(row_dict)
    else:
        # For other orient formats, do a simpler approach
        result = {}
        for col in df_copy.columns:
            result[col] = df_copy[col].apply(lambda x: None if pd.isna(x) else x).tolist()

    return result

# Custom JSON encoder to handle pandas NaT and numpy types
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        try:
            if obj is None:
                return None
            if pd.isna(obj):
                return None
            if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, np.floating):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (pd.DataFrame, pd.Series)):
                return pandas_to_json_safe(obj)
        except Exception as e:
            logger.warning(f"Error in CustomJSONProvider: {e}")
            return None
        return super().default(obj)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint for routes
bp = Blueprint('app', __name__)

# Set up configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
SAMPLE_FOLDER = 'sample_files'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create necessary directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

# Sample files information
SAMPLE_FILES = [
    {
        'name': 'Employee Records (Excel)',
        'filename': 'employee_data.xlsx',
        'description': 'Employee information with mixed phone formats, salary formatting issues, and inconsistent boolean values'
    },
    {
        'name': 'Sales Data (Excel)',
        'filename': 'sales_data.xlsx',
        'description': 'Sales transactions with currency formatting issues, multiple date formats, and inconsistent status values'
    },
    {
        'name': 'Malformed Data (Excel)',
        'filename': 'malformed_data.xlsx',
        'description': 'Intentionally problematic data with mixed types, inconsistent dates, and duplicate rows to test cleaning capabilities'
    },
    {
        'name': 'Sample Products (Excel)',
        'filename': 'sample_products.xlsx',
        'description': 'Product catalog with inconsistent categories and missing stock information'
    },
    {
        'name': 'Employee Data (CSV)',
        'filename': 'employee_data.csv',
        'description': 'CSV version of employee data with formatting inconsistencies'
    },
    {
        'name': 'Sales Data (CSV)',
        'filename': 'sales_data.csv',
        'description': 'CSV version of sales transactions with multiple formatting issues'
    }
]

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    """Render the main page"""
    # Get recent cleaning jobs from the database
    recent_jobs = CleaningJob.query.order_by(CleaningJob.created_at.desc()).limit(5).all()
    return render_template('index.html', sample_files=SAMPLE_FILES, recent_jobs=recent_jobs)

@bp.route('/jobs')
def list_jobs():
    """List all cleaning jobs"""
    jobs = CleaningJob.query.order_by(CleaningJob.created_at.desc()).all()
    return jsonify({
        'jobs': [job.to_dict() for job in jobs]
    })

@bp.route('/use-sample/<filename>')
def use_sample(filename):
    """Copy a sample file to the uploads folder and process it"""
    upload_path = None
    try:
        # Prevent path traversal
        if filename != secure_filename(filename):
            logger.error(f"Invalid sample filename requested: {filename}")
            return jsonify({'error': 'Invalid sample filename'}), 400

        # Verify the requested sample file exists
        sample_path = os.path.join(SAMPLE_FOLDER, filename)
        if not os.path.exists(sample_path):
            logger.error(f"Sample file not found: {filename}")
            return jsonify({'error': 'The requested sample file does not exist'}), 404

        # Copy the sample file to the uploads directory
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        shutil.copy2(sample_path, upload_path)
        logger.info(f"Sample file copied to uploads: {filename}")

        # Process the file just like a regular upload
        saved_files_paths = [upload_path]

        # Set up default cleaning options
        # Get cleaning options from query parameters
        cleaning_options = {
            'remove_nulls': request.args.get('removeNulls', 'true').lower() == 'true',
            'remove_duplicates': request.args.get('removeDuplicates', 'true').lower() == 'true',
            'standardize_text': request.args.get('standardizeText', 'true').lower() == 'true',
            'fill_numerics': request.args.get('fillNumerics', 'true').lower() == 'true',
            'fix_dates': request.args.get('fixDates', 'true').lower() == 'true',
            'trim_whitespace': request.args.get('trimWhitespace', 'true').lower() == 'true',
            'fix_phone_numbers': request.args.get('fixPhoneNumbers', 'true').lower() == 'true',
            'fix_emails': request.args.get('fixEmails', 'true').lower() == 'true',
            'fix_boolean_values': request.args.get('fixBooleanValues', 'true').lower() == 'true',
            'extract_numeric_from_text': request.args.get('extractNumericFromText', 'true').lower() == 'true',
            'normalize_text': request.args.get('normalizeText', 'false').lower() == 'true'
        }

        # Load and merge data
        logger.info("Loading and merging data from sample file")
        merged_df = data_loader.load_and_merge_data(saved_files_paths)

        if merged_df is None or merged_df.empty:
            if upload_path and os.path.exists(upload_path):
                os.remove(upload_path)
            return jsonify({'error': 'Could not extract data from the sample file. The file might be corrupt or in an unsupported format.'}), 500

        try:
            # Get sample of original data (first 5 rows) using our custom function
            preview_df = merged_df.head(5)
            original_sample = pandas_to_json_safe(preview_df)
            column_info = {
                'columns': merged_df.columns.tolist(),
                'dtypes': merged_df.dtypes.astype(str).to_dict()
            }
        except Exception as e:
            logger.error(f"Error preparing original data sample: {e}")
            original_sample = []
            column_info = {'columns': [], 'dtypes': {}}

        # Clean data with options
        logger.info("Cleaning sample data")
        try:
            cleaned_df, cleaning_stats = cleaner.clean_data(merged_df, options=cleaning_options)

            if cleaned_df is None or cleaned_df.empty:
                # Return the original data if cleaning fails completely
                logger.warning("Cleaning returned empty DataFrame, using original")
                cleaned_df = merged_df
                cleaning_stats = {
                    'original_rows': len(merged_df),
                    'cleaned_rows': len(merged_df),
                    'columns': merged_df.shape[1],
                    'nulls_removed': 0,
                    'duplicates_removed': 0,
                    'dates_fixed': 0,
                    'numerics_fixed': 0,
                    'missing_values_filled': 0,
                    'percent_reduced': 0,
                    'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        except Exception as clean_err:
            logger.error(f"Error during data cleaning: {clean_err}")
            # If cleaning fails, use the original data
            cleaned_df = merged_df
            cleaning_stats = {
                'original_rows': len(merged_df),
                'cleaned_rows': len(merged_df),
                'columns': merged_df.shape[1],
                'nulls_removed': 0,
                'duplicates_removed': 0,
                'dates_fixed': 0,
                'numerics_fixed': 0,
                'missing_values_filled': 0,
                'percent_reduced': 0,
                'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        # Get sample of cleaned data
        try:
            cleaned_preview = cleaned_df.head(5)
            cleaned_sample = pandas_to_json_safe(cleaned_preview)
            cleaned_column_info = {
                'columns': cleaned_df.columns.tolist(),
                'dtypes': cleaned_df.dtypes.astype(str).to_dict()
            }
        except Exception as e:
            logger.error(f"Error preparing cleaned data sample: {e}")
            cleaned_sample = []
            cleaned_column_info = {'columns': [], 'dtypes': {}}

        # Save cleaned data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"cleaned_{filename.split('.')[0]}_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save the cleaned data to Excel, with fallback to CSV
        try:
            logger.info(f"Saving cleaned sample data to {output_path}")
            cleaned_df.to_excel(output_path, index=False, engine='openpyxl')
        except Exception as excel_err:
            logger.error(f"Error saving Excel file: {excel_err}")
            # Fallback to CSV if Excel fails
            csv_filename = output_filename.replace('.xlsx', '.csv')
            csv_path = os.path.join(OUTPUT_FOLDER, csv_filename)
            cleaned_df.to_csv(csv_path, index=False)
            output_filename = csv_filename
            logger.info(f"Saved as CSV instead: {csv_path}")

        # Create a new cleaning job record
        try:
            new_job = CleaningJob(
                job_name=f"Sample: {filename}",
                original_filename=filename,
                output_filename=output_filename,
                original_rows=int(cleaning_stats['original_rows']),
                cleaned_rows=int(cleaning_stats['cleaned_rows']),
                columns_count=int(cleaning_stats['columns']),
                missing_values_filled=int(cleaning_stats.get('missing_values_filled', 0)),
                duplicates_removed=int(cleaning_stats.get('duplicates_removed', 0))
            )

            # Add and commit to database
            db.session.add(new_job)
            db.session.commit()
            job_id = new_job.id
            logger.info(f"Cleaning job saved to database with ID: {job_id}")
        except Exception as db_err:
            logger.error(f"Error saving job to database: {db_err}")
            job_id = None

        # Cleanup uploaded files
        if upload_path and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
                logger.debug(f"Cleaned up sample file: {upload_path}")
            except Exception as e:
                logger.error(f"Failed to remove temporary file {upload_path}: {e}")

        return jsonify({
            'message': 'Sample file processed successfully',
            'download_filename': output_filename,
            'row_count': len(cleaned_df),
            'original_sample': original_sample,
            'cleaned_sample': cleaned_sample,
            'original_columns': column_info,
            'cleaned_columns': cleaned_column_info,
            'stats': cleaning_stats,
            'job_id': job_id
        }), 200

    except Exception as e:
        logger.error(f"Error processing sample file: {e}", exc_info=True)
        # Clean up the upload file if it exists
        if upload_path and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except:
                pass
        return jsonify({'error': f'Error processing sample file: {str(e)}'}), 500

@bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads, process them, and return results"""
    try:
        logger.info("Upload request received")
        # Don't log the entire form data as it might be too large
        logger.info("Processing upload request")

        # Check if 'files' is in the request
        if 'files' not in request.files:
            logger.warning("No file part in the request")
            return jsonify({'error': 'No files found in request. Please select at least one file.'}), 400

        files = request.files.getlist('files')
        logger.info(f"Number of files received: {len(files)}")

        # Check if files list is empty or contains only files with empty filenames
        if not files or all(not file or not file.filename or file.filename == '' for file in files):
            logger.warning("No selected files or empty filenames")
            return jsonify({'error': 'No valid files selected. Please choose at least one CSV or Excel file.'}), 400

        # Log file details
        for i, file in enumerate(files):
            if file and file.filename:
                logger.info(f"File {i+1}: {file.filename}, Content type: {file.content_type}")
            else:
                logger.info(f"File {i+1}: Invalid or no filename")

        # Get cleaning options with safe defaults
        try:
            cleaning_options = {
                'remove_nulls': request.form.get('removeNulls', 'true').lower() == 'true',
                'remove_duplicates': request.form.get('removeDuplicates', 'true').lower() == 'true',
                'standardize_text': request.form.get('standardizeText', 'true').lower() == 'true',
                'fill_numerics': request.form.get('fillNumerics', 'true').lower() == 'true',
                'fix_dates': request.form.get('fixDates', 'true').lower() == 'true',
                'trim_whitespace': request.form.get('trimWhitespace', 'true').lower() == 'true',
                'fix_phone_numbers': request.form.get('fixPhoneNumbers', 'true').lower() == 'true',
                'fix_emails': request.form.get('fixEmails', 'true').lower() == 'true',
                'fix_boolean_values': request.form.get('fixBooleanValues', 'true').lower() == 'true',
                'extract_numeric_from_text': request.form.get('extractNumericFromText', 'true').lower() == 'true',
                'normalize_text': request.form.get('normalizeText', 'false').lower() == 'true'
            }
        except Exception as e:
            logger.error(f"Error parsing cleaning options: {e}")
            # Use safe defaults if there's an error parsing options
            cleaning_options = {
                'remove_nulls': True,
                'remove_duplicates': True,
                'standardize_text': True,
                'fill_numerics': True,
                'fix_dates': True,
                'trim_whitespace': True,
                'fix_phone_numbers': True,
                'fix_emails': True,
                'fix_boolean_values': True,
                'extract_numeric_from_text': True,
                'normalize_text': False
            }

        logger.info(f"Cleaning options: {cleaning_options}")

        saved_files_paths = []
        original_filenames = []

        # Save valid files
        for file in files:
            try:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    logger.info(f"Processing file: {filename}")

                    # Generate a unique filename to avoid conflicts
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    unique_filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

                    # Make sure the upload directory exists
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                    # Save the file
                    try:
                        file.save(filepath)
                        logger.info(f"File saved successfully: {filepath}")

                        # Verify the file was saved correctly
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            original_filenames.append(filename)
                            saved_files_paths.append(filepath)
                            logger.info(f"File verified: {filepath}, Size: {os.path.getsize(filepath)} bytes")
                        else:
                            logger.error(f"File save verification failed: {filepath}")
                            return jsonify({'error': f'Error saving file {filename}. Please try again.'}), 500
                    except Exception as save_err:
                        logger.error(f"Error saving file {filename}: {save_err}", exc_info=True)
                        return jsonify({'error': f'Error saving file {filename}: {str(save_err)}. Please try again.'}), 500
                else:
                    if file and file.filename:
                        logger.warning(f"Invalid file format: {file.filename}")
                    else:
                        logger.warning("Invalid file: unnamed or no filename")
            except Exception as e:
                logger.error(f"Error processing file: {e}", exc_info=True)
                return jsonify({'error': f'Error processing file: {str(e)}. Please try again.'}), 500

        # Check if any valid files were saved
        if not saved_files_paths:
            return jsonify({'error': 'No valid files were uploaded. Please use CSV or Excel (.xlsx, .xls) files only.'}), 400

        try:
            # Load and merge data
            logger.info("Loading and merging data")
            try:
                merged_df = data_loader.load_and_merge_data(saved_files_paths)

                if merged_df is None or merged_df.empty:
                    # Clean up any saved files before returning error
                    for filepath in saved_files_paths:
                        try:
                            if os.path.exists(filepath):
                                os.remove(filepath)
                        except Exception as e:
                            logger.error(f"Error removing file {filepath}: {e}")
                    return jsonify({'error': 'Could not extract data from the uploaded files. Please check file contents and try again.'}), 400
            except Exception as e:
                logger.error(f"Error in load_and_merge_data: {e}", exc_info=True)
                # Clean up any saved files before returning error
                for filepath in saved_files_paths:
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception as cleanup_err:
                        logger.error(f"Error removing file {filepath}: {cleanup_err}")
                return jsonify({'error': f'Error processing files: {str(e)}. Please check your files and try again.'}), 500

            # Handle very large files - limit preview to 5 rows max
            preview_df = merged_df.head(5)

            # Get sample of original data using our custom function
            try:
                original_sample = pandas_to_json_safe(preview_df)
                column_info = {
                    'columns': merged_df.columns.tolist(),
                    'dtypes': merged_df.dtypes.astype(str).to_dict()
                }
            except Exception as e:
                logger.error(f"Error preparing original data sample: {e}")
                original_sample = []
                column_info = {'columns': [], 'dtypes': {}}

            # Clean data with options
            logger.info("Cleaning data with options")
            cleaned_df, cleaning_stats = cleaner.clean_data(merged_df, options=cleaning_options)

            if cleaned_df is None or cleaned_df.empty:
                # Return the original data if cleaning fails completely
                logger.warning("Cleaning returned empty DataFrame, using original")
                cleaned_df = merged_df
                cleaning_stats = {
                    'original_rows': len(merged_df),
                    'cleaned_rows': len(merged_df),
                    'columns': merged_df.shape[1],
                    'nulls_removed': 0,
                    'duplicates_removed': 0,
                    'dates_fixed': 0,
                    'numerics_fixed': 0,
                    'missing_values_filled': 0,
                    'percent_reduced': 0,
                    'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            # Get sample of cleaned data (first 5 rows) using our custom function
            try:
                cleaned_preview = cleaned_df.head(5)
                cleaned_sample = pandas_to_json_safe(cleaned_preview)
                cleaned_column_info = {
                    'columns': cleaned_df.columns.tolist(),
                    'dtypes': cleaned_df.dtypes.astype(str).to_dict()
                }
            except Exception as e:
                logger.error(f"Error preparing cleaned data sample: {e}")
                cleaned_sample = []
                cleaned_column_info = {'columns': [], 'dtypes': {}}

            # Save cleaned data
            output_filename = f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            logger.info(f"Saving cleaned data to {output_path}")
            try:
                cleaned_df.to_excel(output_path, index=False, engine='openpyxl')
            except Exception as excel_err:
                logger.error(f"Error saving Excel file: {excel_err}")
                # Fallback to CSV if Excel fails
                csv_filename = output_filename.replace('.xlsx', '.csv')
                csv_path = os.path.join(OUTPUT_FOLDER, csv_filename)
                cleaned_df.to_csv(csv_path, index=False)
                output_filename = csv_filename
                logger.info(f"Saved as CSV instead: {csv_path}")

            # Create a new cleaning job record
            try:
                job_name = f"Upload: {', '.join(original_filenames[:2])}"
                if len(original_filenames) > 2:
                    job_name += f" and {len(original_filenames) - 2} more"

                new_job = CleaningJob(
                    job_name=job_name,
                    original_filename=', '.join(original_filenames),
                    output_filename=output_filename,
                    original_rows=int(cleaning_stats['original_rows']),
                    cleaned_rows=int(cleaning_stats['cleaned_rows']),
                    columns_count=int(cleaning_stats['columns']),
                    missing_values_filled=int(cleaning_stats.get('missing_values_filled', 0)),
                    duplicates_removed=int(cleaning_stats.get('duplicates_removed', 0))
                )

                # Add and commit to database
                db.session.add(new_job)
                db.session.commit()
                job_id = new_job.id
                logger.info(f"Cleaning job saved to database with ID: {job_id}")
            except Exception as db_err:
                logger.error(f"Error saving job to database: {db_err}")
                job_id = None

            # Cleanup uploaded files
            for filepath in saved_files_paths:
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.debug(f"Cleaned up file: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to remove temporary file {filepath}: {e}")

            return jsonify({
                'message': 'Files processed successfully',
                'download_filename': output_filename,
                'row_count': len(cleaned_df),
                'original_sample': original_sample,
                'cleaned_sample': cleaned_sample,
                'original_columns': column_info,
                'cleaned_columns': cleaned_column_info,
                'stats': cleaning_stats,
                'job_id': job_id
            }), 200

        except Exception as e:
            logger.error(f"Error processing files: {e}", exc_info=True)
            # Clean up any saved files if processing fails
            for filepath in saved_files_paths:
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except:
                    pass

            return jsonify({'error': f'Error processing files: {str(e)}. Please check your files and try again.'}), 500

    except Exception as outer_e:
        logger.error(f"Unexpected error in upload route: {outer_e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Handle file downloads"""
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return jsonify({'error': 'File not found'}), 404

# Initialize function to register our Blueprint with a Flask app
def init_app(app):
    app.register_blueprint(bp)

    # Register custom JSON provider to handle pandas and numpy types
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)

    # Set app config variables
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
    app.config['SAMPLE_FOLDER'] = SAMPLE_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 400 * 1024 * 1024  # Limit uploads to 400MB

    return app

# Code update: 2025-04-17 20:28:34

# Code update: 2025-04-17 20:28:35

# Code update: 2025-04-17 20:28:36

# Code update: 2025-04-17 20:28:36

# Code update: 2025-04-17 20:28:40

# Code update: 2025-04-17 20:28:40

# Code update: 2025-04-17 20:28:42

# Code update: 2025-04-17 20:28:43

# Code update: 2025-04-17 20:28:43

# Code update: 2025-04-17 20:28:44

# Code update: 2025-04-17 20:28:44

# Code update: 2025-04-17 20:28:46

# Code update: 2025-04-17 20:28:48

# Code update: 2025-04-17 20:28:49

# Code update: 2025-04-17 20:28:49

# Code update: 2025-04-17 20:28:50

# Code update: 2025-04-17 20:28:51

# Code update: 2025-04-17 20:28:51

# Code update: 2025-04-17 20:28:53

# Code update: 2025-04-17 20:28:53

# Code update: 2025-04-17 20:28:55

# Code update: 2025-04-17 20:28:55

# Code update: 2025-04-17 20:28:56

# Code update: 2025-04-17 20:28:58

# Code update: 2025-04-17 20:29:01

# Code update: 2025-04-17 20:29:02

# Code update: 2025-04-17 20:29:02

# Code update: 2025-04-17 20:29:03

# Code update: 2025-04-17 20:29:04

# Code update: 2025-04-17 20:29:04

# Code update: 2025-04-17 20:29:06

# Code update: 2025-04-17 20:29:07

# Code update: 2025-04-17 20:29:08

# Code update: 2025-04-17 20:29:08

# Code update: 2025-04-17 20:29:09

# Code update: 2025-04-17 20:29:09

# Code update: 2025-04-17 20:29:10

# Code update: 2025-04-17 20:29:11

# Code update: 2025-04-17 20:29:12

# Code update: 2025-04-17 20:29:13

# Code update: 2025-04-17 20:29:13

# Code update: 2025-04-17 20:29:14

# Code update: 2025-04-17 20:29:15

# Code update: 2025-04-17 20:29:16

# Code update: 2025-04-17 20:29:18

# Code update: 2025-04-17 20:29:20

# Code update: 2025-04-17 20:29:22

# Code update: 2025-04-17 20:29:23

# Code update: 2025-04-17 20:29:24

# Code update: 2025-04-17 20:29:25

# Code update: 2025-04-17 20:29:25

# Code update: 2025-04-17 20:29:28

# Code update: 2025-04-17 20:29:28

# Code update: 2025-04-17 20:29:29

# Code update: 2025-04-17 20:29:30

# Code update: 2025-04-17 20:29:47

# Code update: 2025-04-17 20:29:48

# Code update: 2025-04-17 20:30:17

# Code update: 2025-04-17 20:30:21

# Code update: 2025-04-17 20:30:23

# Code update: 2025-04-17 20:30:23

# Code update: 2025-04-17 20:30:27

# Code update: 2025-04-17 20:30:29

# Code update: 2025-04-17 20:30:31

# Code update: 2025-04-17 20:30:31

# Code update: 2025-04-17 20:30:32

# Code update: 2025-04-17 20:30:33

# Code update: 2025-04-17 20:30:34

# Code update: 2025-04-17 20:30:34

# Code update: 2025-04-17 20:30:36

# Code update: 2025-04-17 20:30:37

# Code update: 2025-04-17 20:30:37

# Code update: 2025-04-17 20:30:38

# Code update: 2025-04-17 20:30:38

# Code update: 2025-04-17 20:30:38

# Code update: 2025-04-17 20:30:41

# Code update: 2025-04-17 20:30:43

# Code update: 2025-04-17 20:30:46

# Code update: 2025-04-17 20:30:47

# Code update: 2025-04-17 20:30:49

# Code update: 2025-04-17 20:30:49

# Code update: 2025-04-17 20:30:50

# Code update: 2025-04-17 20:30:50

# Code update: 2025-04-17 20:30:51

# Code update: 2025-04-17 20:30:53

# Code update: 2025-04-17 20:30:57

# Code update: 2025-04-17 20:31:01

# Code update: 2025-04-17 20:31:01

# Code update: 2025-04-17 20:31:02

# Code update: 2025-04-17 20:31:04

# Code update: 2025-04-17 20:31:06

# Code update: 2025-04-17 20:31:07

# Code update: 2025-04-17 20:31:07

# Code update: 2025-04-17 20:31:09

# Code update: 2025-04-17 20:31:10

# Code update: 2025-04-17 20:31:11

# Code update: 2025-04-17 20:31:11

# Code update: 2025-04-17 20:31:15

# Code update: 2025-04-17 20:31:15

# Code update: 2025-04-17 20:31:16

# Code update: 2025-04-17 20:31:18

# Code update: 2025-04-17 20:31:20

# Code update: 2025-04-17 20:31:21

# Code update: 2025-04-17 20:31:22

# Code update: 2025-04-17 20:31:23

# Code update: 2025-04-17 20:31:23

# Code update: 2025-04-17 20:31:24

# Code update: 2025-04-17 20:31:24

# Code update: 2025-04-17 20:31:27

# Code update: 2025-04-17 20:31:27

# Code update: 2025-04-17 20:31:29

# Code update: 2025-04-17 20:31:29

# Code update: 2025-04-17 20:31:31

# Code update: 2025-04-17 20:31:31

# Code update: 2025-04-17 20:31:32

# Code update: 2025-04-17 20:31:35

# Code update: 2025-04-17 20:31:35

# Code update: 2025-04-17 20:31:38

# Code update: 2025-04-17 20:31:40

# Code update: 2025-04-17 20:31:40

# Code update: 2025-04-17 20:31:41

# Code update: 2025-04-17 20:31:48

# Code update: 2025-04-17 20:31:50

# Code update: 2025-04-17 20:31:52

# Code update: 2025-04-17 20:31:53

# Code update: 2025-04-17 20:31:54

# Code update: 2025-04-17 20:31:56

# Code update: 2025-04-17 20:31:58

# Code update: 2025-04-17 20:32:00

# Code update: 2025-04-17 20:32:01

# Code update: 2025-04-17 20:32:02

# Code update: 2025-04-17 20:32:02

# Code update: 2025-04-17 20:32:04

# Code update: 2025-04-17 20:32:05

# Code update: 2025-04-17 20:32:06

# Code update: 2025-04-17 20:32:07

# Code update: 2025-04-17 20:32:08

# Code update: 2025-04-17 20:32:11

# Code update: 2025-04-17 20:32:11

# Code update: 2025-04-17 20:32:12

# Code update: 2025-04-17 20:32:13

# Code update: 2025-04-17 20:32:14

# Code update: 2025-04-17 20:32:16

# Code update: 2025-04-17 20:32:16

# Code update: 2025-04-17 20:32:16

# Code update: 2025-04-17 20:32:17

# Code update: 2025-04-17 20:32:17

# Code update: 2025-04-17 20:32:21

# Code update: 2025-04-17 20:32:21

# Code update: 2025-04-17 20:32:23

# Code update: 2025-04-17 20:32:24

# Code update: 2025-04-17 20:32:25

# Code update: 2025-04-17 20:32:26

# Code update: 2025-04-17 20:32:29

# Code update: 2025-04-17 20:32:30

# Code update: 2025-04-17 20:32:30

# Code update: 2025-04-17 20:32:30

# Code update: 2025-04-17 20:32:32

# Code update: 2025-04-17 20:32:32

# Code update: 2025-04-17 20:32:34

# Code update: 2025-04-17 20:32:35

# Code update: 2025-04-17 20:32:36

# Code update: 2025-04-17 20:57:09

# Code update: 2025-04-17 20:57:10

# Code update: 2025-04-17 20:57:11

# Code update: 2025-04-17 20:57:12

# Code update: 2025-04-17 20:57:15

# Code update: 2025-04-17 20:57:16

# Code update: 2025-04-17 20:57:18

# Code update: 2025-04-17 20:57:21

# Code update: 2025-04-17 20:57:21

# Code update: 2025-04-17 20:57:24

# Code update: 2025-04-17 20:57:25

# Code update: 2025-04-17 20:57:26

# Code update: 2025-04-17 20:57:26

# Code update: 2025-04-17 20:57:27

# Code update: 2025-04-17 20:57:27

# Code update: 2025-04-17 20:57:28

# Code update: 2025-04-17 20:57:30

# Code update: 2025-04-17 20:57:30

# Code update: 2025-04-17 20:57:31

# Code update: 2025-04-17 20:57:33

# Code update: 2025-04-17 20:57:33

# Code update: 2025-04-17 20:57:34

# Code update: 2025-04-17 20:57:35

# Code update: 2025-04-17 20:57:36

# Code update: 2025-04-17 20:57:36

# Code update: 2025-04-17 20:57:37

# Code update: 2025-04-17 20:57:40

# Code update: 2025-04-17 20:57:41

# Code update: 2025-04-17 20:57:43

# Code update: 2025-04-17 20:57:45

# Code update: 2025-04-17 20:57:46

# Code update: 2025-04-17 20:57:47

# Code update: 2025-04-17 20:57:48

# Code update: 2025-04-17 20:57:49

# Code update: 2025-04-17 20:57:57

# Code update: 2025-04-17 20:57:59

# Code update: 2025-04-17 20:58:01
