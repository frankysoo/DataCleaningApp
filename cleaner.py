import pandas as pd
import numpy as np
import logging
import re
import string
from datetime import datetime
import unicodedata

# Configure logging
logger = logging.getLogger(__name__)

def extract_numeric_value(value):
    """
    Extract numeric value from strings containing currency symbols, commas, etc.
    E.g. "$1,234.56" -> 1234.56, "€50,00" -> 50.00

    Args:
        value: The value to extract numeric part from

    Returns:
        Extracted float value or None if extraction fails
    """
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    # Remove currency symbols, spaces, and other non-numeric characters except dots and commas
    value = re.sub(r'[^\d,.+-]', '', str(value))

    # Handle European style numbers (comma as decimal separator)
    if ',' in value and '.' in value:
        # If both present, the last one is probably the decimal separator
        if value.rindex(',') > value.rindex('.'):
            value = value.replace('.', '')  # Remove thousand separators
            value = value.replace(',', '.')  # Convert decimal separator
        else:
            value = value.replace(',', '')  # Remove thousand separators
    elif ',' in value and '.' not in value:
        # If only comma, assume it's decimal separator (European style)
        value = value.replace(',', '.')

    # Try to convert to float
    try:
        return float(value)
    except ValueError:
        return None

def standardize_phone_number(phone):
    """
    Standardize phone number formats

    Args:
        phone: Phone number string

    Returns:
        Standardized phone number or original if it cannot be standardized
    """
    if pd.isna(phone) or not isinstance(phone, str):
        return phone

    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # Check if we have a reasonable number of digits
    if len(digits) < 7:  # Too short to be a phone number
        return phone

    # Format based on length
    if len(digits) == 10:  # Standard US number
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):  # US number with country code
        return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    else:
        # Just add hyphens for readability
        return '-'.join([digits[i:i+3] for i in range(0, len(digits), 3)])

def standardize_email(email):
    """
    Basic email format standardization and validation

    Args:
        email: Email string

    Returns:
        Standardized email or original if it cannot be standardized
    """
    if pd.isna(email) or not isinstance(email, str):
        return email

    # Basic email validation pattern
    email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    # Clean the email
    email = email.strip().lower()

    # Fix common issues
    email = re.sub(r'\s+', '', email)  # Remove whitespace
    email = email.replace('@@', '@')   # Fix double @ symbols

    # Check if valid after fixes
    if email_pattern.match(email):
        return email

    # Try some simple fixes for common issues
    if '@' not in email:
        # Missing @ symbol entirely
        return email

    email_parts = email.split('@')
    if len(email_parts) != 2:
        # Multiple @ symbols or other issues
        return email

    username, domain = email_parts

    # Check if domain needs a suffix
    if '.' not in domain:
        return email

    return email

def normalize_text(text):
    """
    Normalize text by removing accents, standardizing case, etc.

    Args:
        text: Text string to normalize

    Returns:
        Normalized text
    """
    if pd.isna(text) or not isinstance(text, str):
        return text

    # Convert to lowercase
    text = text.lower()

    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Convert accented characters to ASCII
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])

    return text

def detect_boolean_values(value):
    """
    Detect and standardize boolean values

    Args:
        value: The value to check for boolean representation

    Returns:
        True, False, or the original value
    """
    if pd.isna(value):
        return value

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        if value == 1:
            return True
        elif value == 0:
            return False
        return value

    if isinstance(value, str):
        value_lower = value.lower().strip()

        # Check for various textual boolean representations
        if value_lower in ('yes', 'y', 'true', 't', '1', 'on', 'enabled', 'available'):
            return True
        elif value_lower in ('no', 'n', 'false', 'f', '0', 'off', 'disabled', 'unavailable'):
            return False

    return value

def detect_and_parse_date(date_str):
    """
    Advanced date format detection and parsing

    Args:
        date_str: Date string to parse

    Returns:
        Pandas Timestamp or None if parsing fails
    """
    if pd.isna(date_str):
        return None

    if isinstance(date_str, pd.Timestamp):
        return date_str

    original_value = date_str

    # Standardize date string before parsing
    if isinstance(date_str, str):
        # Replace various separators with standard ones
        date_str = re.sub(r'[.\\/]', '-', date_str)

        # Handle textual month representations
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }

        # Try to convert month names to numbers
        for month_name, month_num in month_map.items():
            # Match full month names or abbreviations with various patterns
            date_str = re.sub(rf'\b{month_name}[a-z]*\b', month_num, date_str.lower())

        # Remove ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

        # Remove any remaining non-numeric, non-separator characters
        date_str = re.sub(r'[^\d\-:/\s]', '', date_str)

        # Try to parse with pandas
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            try:
                return pd.to_datetime(original_value, errors='coerce')
            except:
                return None
    else:
        # For non-string values, let pandas handle it
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            return None

def clean_data(df, options=None):
    """
    Clean the input DataFrame by applying various cleaning operations

    Args:
        df: Pandas DataFrame to clean
        options: Dictionary of cleaning options:
            - remove_nulls: Drop rows where all values are NaN (Default: True)
            - remove_duplicates: Remove duplicate rows (Default: True)
            - standardize_text: Standardize categorical text columns (Default: True)
            - fill_numerics: Fill numeric nulls with 0 (Default: True)
            - fix_dates: Try to fix date formats (Default: True)
            - trim_whitespace: Trim whitespace from text fields (Default: True)
            - fix_phone_numbers: Standardize phone number formats (Default: True)
            - fix_emails: Standardize and validate email addresses (Default: True)
            - fix_boolean_values: Standardize boolean values (Default: True)
            - extract_numeric_from_text: Extract numeric values from text (Default: True)
            - normalize_text: Normalize text by removing accents, etc. (Default: False)

    Returns:
        Cleaned pandas DataFrame and stats dictionary
    """
    # Validate input DataFrame
    if df is None:
        logger.error("Input DataFrame is None")
        return pd.DataFrame(), {
            'original_rows': 0,
            'cleaned_rows': 0,
            'columns': 0,
            'nulls_removed': 0,
            'duplicates_removed': 0,
            'dates_fixed': 0,
            'numerics_fixed': 0,
            'missing_values_filled': 0,
            'phone_numbers_fixed': 0,
            'emails_fixed': 0,
            'booleans_fixed': 0,
            'extracted_numeric_values': 0,
            'percent_reduced': 0,
            'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    try:
        # Check if DataFrame is valid
        if not isinstance(df, pd.DataFrame):
            logger.error(f"Input is not a DataFrame, got {type(df)}")
            return pd.DataFrame(), {
                'original_rows': 0,
                'cleaned_rows': 0,
                'columns': 0,
                'nulls_removed': 0,
                'duplicates_removed': 0,
                'dates_fixed': 0,
                'numerics_fixed': 0,
                'missing_values_filled': 0,
                'phone_numbers_fixed': 0,
                'emails_fixed': 0,
                'booleans_fixed': 0,
                'extracted_numeric_values': 0,
                'percent_reduced': 0,
                'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        logger.error(f"Error validating DataFrame: {e}")
        return pd.DataFrame(), {
            'original_rows': 0,
            'cleaned_rows': 0,
            'columns': 0,
            'nulls_removed': 0,
            'duplicates_removed': 0,
            'dates_fixed': 0,
            'numerics_fixed': 0,
            'missing_values_filled': 0,
            'phone_numbers_fixed': 0,
            'emails_fixed': 0,
            'booleans_fixed': 0,
            'extracted_numeric_values': 0,
            'percent_reduced': 0,
            'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    if df is None or df.empty:
        logger.warning("Input DataFrame is empty or None")
        return pd.DataFrame(), {
            'original_rows': 0,
            'cleaned_rows': 0,
            'columns': 0,
            'nulls_removed': 0,
            'duplicates_removed': 0,
            'dates_fixed': 0,
            'numerics_fixed': 0,
            'missing_values_filled': 0,
            'phone_numbers_fixed': 0,
            'emails_fixed': 0,
            'booleans_fixed': 0,
            'extracted_numeric_values': 0,
            'percent_reduced': 0,
            'cleaning_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    logger.info(f"Starting data cleaning on DataFrame with {len(df)} rows and {df.shape[1]} columns")

    # Set default options if not provided
    if options is None:
        options = {
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

    # Initialize cleaning statistics
    stats = {
        'original_rows': len(df),
        'columns': df.shape[1],
        'nulls_removed': 0,
        'duplicates_removed': 0,
        'dates_fixed': 0,
        'numerics_fixed': 0,
        'missing_values_filled': 0,
        'phone_numbers_fixed': 0,
        'emails_fixed': 0,
        'booleans_fixed': 0,
        'extracted_numeric_values': 0
    }

    try:
        # Make a copy to avoid modifying the original
        cleaned_df = df.copy()

        # Replace any infinity values with NaN for stability
        cleaned_df = cleaned_df.replace([np.inf, -np.inf], np.nan)

        # Step 1: Handle missing values
        if options.get('remove_nulls', True):
            try:
                # Count nulls before removal
                initial_rows = len(cleaned_df)
                # Drop rows where all values are NaN
                cleaned_df.dropna(how='all', inplace=True)
                stats['nulls_removed'] = initial_rows - len(cleaned_df)
                logger.info(f"After dropping all-NaN rows: {len(cleaned_df)} rows remain")
            except Exception as e:
                logger.error(f"Error removing null rows: {e}")

        # Step 2: Remove duplicates
        if options.get('remove_duplicates', True):
            try:
                initial_rows = len(cleaned_df)
                cleaned_df.drop_duplicates(inplace=True)
                stats['duplicates_removed'] = initial_rows - len(cleaned_df)
                logger.info(f"Removed {stats['duplicates_removed']} duplicate rows")
            except Exception as e:
                logger.error(f"Error removing duplicates: {e}")

        # Step 3: First pass to identify column types and patterns
        column_types = {}

        for column in cleaned_df.columns:
            try:
                # Skip columns with all NaN values
                if cleaned_df[column].isna().all():
                    continue

                # Get non-empty values for analysis
                non_empty_values = cleaned_df[column].dropna()
                if len(non_empty_values) == 0:
                    continue

                sample_values = non_empty_values.head(100)  # Sample for pattern detection

                # Detect column type based on patterns

                # Check for date patterns in string columns
                if cleaned_df[column].dtype == 'object':
                    # Date patterns
                    date_patterns = [
                        # ISO format: 2023-04-07
                        r'^\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}$',
                        # US format: 04/07/2023
                        r'^\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4}$',
                        # Short year: 04/07/23
                        r'^\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2}$',
                        # Month name: April 7, 2023
                        r'^[a-zA-Z]{3,9}\s+\d{1,2}[,]?\s+\d{4}$',
                        # Day with ordinal: 7th April 2023
                        r'^\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]{3,9}\s+\d{4}$'
                    ]

                    # Count date-like values
                    date_count = 0
                    for val in sample_values:
                        if isinstance(val, str):
                            if any(re.match(pattern, val.strip()) for pattern in date_patterns):
                                date_count += 1

                    date_ratio = date_count / len(sample_values) if sample_values.size > 0 else 0

                    if date_ratio > 0.5:
                        column_types[column] = 'date'
                        continue

                    # Email patterns
                    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                    email_count = sum(1 for val in sample_values if isinstance(val, str) and re.match(email_pattern, val.strip()))
                    email_ratio = email_count / len(sample_values) if sample_values.size > 0 else 0

                    if email_ratio > 0.5:
                        column_types[column] = 'email'
                        continue

                    # Phone number patterns
                    phone_patterns = [
                        r'^\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$',  # +1 (555) 123-4567
                        r'^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$',  # 555-123-4567
                        r'^\(\d{3}\)\s?\d{3}[-.\s]?\d{4}$'  # (555) 123-4567
                    ]

                    phone_count = 0
                    for val in sample_values:
                        if isinstance(val, str):
                            if any(re.match(pattern, val.strip()) for pattern in phone_patterns):
                                phone_count += 1

                    phone_ratio = phone_count / len(sample_values) if sample_values.size > 0 else 0

                    if phone_ratio > 0.5:
                        column_types[column] = 'phone'
                        continue

                    # Boolean-like values
                    bool_patterns = ['yes', 'no', 'true', 'false', 'y', 'n', 't', 'f', '1', '0']
                    bool_count = sum(1 for val in sample_values if isinstance(val, str) and val.lower().strip() in bool_patterns)
                    bool_ratio = bool_count / len(sample_values) if sample_values.size > 0 else 0

                    if bool_ratio > 0.7:
                        column_types[column] = 'boolean'
                        continue

                    # Currency/numeric with units
                    currency_pattern = r'^[$€£¥]\s*[\d,]+\.?\d*$|^\d+\.?\d*\s*[$€£¥]$'
                    numeric_with_symbols = sum(1 for val in sample_values
                                           if isinstance(val, str) and (re.match(currency_pattern, val.strip())
                                           or any(c in val for c in "$€£¥%")))

                    if numeric_with_symbols > len(sample_values) * 0.5:
                        column_types[column] = 'numeric_text'
                        continue

                    # Check if it's categorical
                    unique_ratio = non_empty_values.nunique() / len(non_empty_values)
                    if unique_ratio < 0.2:  # Less than 20% unique values
                        column_types[column] = 'categorical'
                    else:
                        column_types[column] = 'text'

                # Already numeric
                elif pd.api.types.is_numeric_dtype(cleaned_df[column]):
                    column_types[column] = 'numeric'

                # Already date
                elif pd.api.types.is_datetime64_dtype(cleaned_df[column]):
                    column_types[column] = 'date'

                # Already boolean
                elif pd.api.types.is_bool_dtype(cleaned_df[column]):
                    column_types[column] = 'boolean'

            except Exception as e:
                logger.error(f"Error detecting type for column '{column}': {e}")
                column_types[column] = 'unknown'

        # Step 4: Apply specific cleaning based on detected column types
        for column, column_type in column_types.items():
            try:
                logger.info(f"Processing column '{column}' detected as type '{column_type}'")

                # Date handling
                if column_type == 'date' and options.get('fix_dates', True):
                    try:
                        original_non_null = cleaned_df[column].count()
                        cleaned_df[column] = cleaned_df[column].apply(detect_and_parse_date)
                        # Count how many valid dates we have after conversion
                        valid_dates = cleaned_df[column].count()
                        if valid_dates >= original_non_null * 0.7:  # If at least 70% converted successfully
                            stats['dates_fixed'] += 1
                            logger.info(f"Successfully converted column '{column}' to dates")
                        else:
                            # Revert if too many failed conversions
                            cleaned_df[column] = df[column]
                            logger.warning(f"Date conversion for '{column}' produced too many NaT values, reverting")
                    except Exception as e:
                        logger.error(f"Error fixing dates in column '{column}': {e}")

                # Email handling
                elif column_type == 'email' and options.get('fix_emails', True):
                    try:
                        cleaned_df[column] = cleaned_df[column].apply(standardize_email)
                        stats['emails_fixed'] += 1
                        logger.info(f"Standardized email formats in column '{column}'")
                    except Exception as e:
                        logger.error(f"Error fixing emails in column '{column}': {e}")

                # Phone number handling
                elif column_type == 'phone' and options.get('fix_phone_numbers', True):
                    try:
                        cleaned_df[column] = cleaned_df[column].apply(standardize_phone_number)
                        stats['phone_numbers_fixed'] += 1
                        logger.info(f"Standardized phone number formats in column '{column}'")
                    except Exception as e:
                        logger.error(f"Error fixing phone numbers in column '{column}': {e}")

                # Boolean handling
                elif column_type == 'boolean' and options.get('fix_boolean_values', True):
                    try:
                        # Store original nulls
                        null_mask = cleaned_df[column].isna()

                        # Apply boolean standardization
                        cleaned_df[column] = cleaned_df[column].apply(detect_boolean_values)

                        # Check if we can convert to actual boolean dtype
                        if cleaned_df.loc[~null_mask, column].apply(lambda x: isinstance(x, bool)).all():
                            # All non-null values are now bool, set dtype
                            cleaned_df[column] = cleaned_df[column].astype('boolean')

                        stats['booleans_fixed'] += 1
                        logger.info(f"Standardized boolean values in column '{column}'")
                    except Exception as e:
                        logger.error(f"Error fixing boolean values in column '{column}': {e}")

                # Numeric text handling (with currency symbols, etc.)
                elif column_type == 'numeric_text' and options.get('extract_numeric_from_text', True):
                    try:
                        # Store original nulls
                        null_mask = cleaned_df[column].isna()

                        # Apply numeric extraction
                        cleaned_df[column] = cleaned_df[column].apply(extract_numeric_value)

                        # If we have at least some successful conversions
                        if cleaned_df[column].apply(lambda x: isinstance(x, (int, float))).any():
                            stats['extracted_numeric_values'] += 1
                            logger.info(f"Extracted numeric values from column '{column}'")
                    except Exception as e:
                        logger.error(f"Error extracting numeric values in column '{column}': {e}")

                # General numeric handling
                elif (column_type == 'numeric' or pd.api.types.is_numeric_dtype(cleaned_df[column])) and options.get('fill_numerics', True):
                    try:
                        # Just handle NaN filling for already numeric columns
                        na_count = cleaned_df[column].isna().sum()
                        if na_count > 0:
                            # Consider using mean/median for appropriate columns
                            if na_count / len(cleaned_df) < 0.3:  # Less than 30% missing
                                # Try to identify if values look like quantities (always positive, similar magnitude)
                                non_na_values = cleaned_df[column].dropna()

                                if (non_na_values >= 0).all() and non_na_values.std() / non_na_values.mean() < 2:
                                    # Fill with mean for numeric measurements
                                    cleaned_df[column] = cleaned_df[column].fillna(non_na_values.mean())
                                    logger.info(f"Filled NaN values in column '{column}' with mean")
                                else:
                                    # Fill with median for numeric ratings or skewed distributions
                                    cleaned_df[column] = cleaned_df[column].fillna(non_na_values.median())
                                    logger.info(f"Filled NaN values in column '{column}' with median")
                            else:
                                # If too many missing, fill with 0
                                cleaned_df[column] = cleaned_df[column].fillna(0)
                                logger.info(f"Filled NaN values in column '{column}' with 0")

                            stats['missing_values_filled'] += na_count
                    except Exception as e:
                        logger.error(f"Error processing numeric column '{column}': {e}")

                # Categorical handling
                elif column_type == 'categorical' and options.get('standardize_text', True):
                    try:
                        # Store original nulls
                        null_mask = cleaned_df[column].isna()

                        # Standardize categories
                        cleaned_df.loc[~null_mask, column] = (cleaned_df
                                                             .loc[~null_mask, column]
                                                             .astype(str)
                                                             .str.lower()
                                                             .str.strip())

                        # If we have a small number of unique values, replace similar ones
                        unique_values = cleaned_df[column].dropna().unique()
                        if len(unique_values) < 20:
                            # Group similar values
                            similarity_groups = {}

                            for val in unique_values:
                                if not isinstance(val, str) or not val:
                                    continue

                                # Find matching group or create new one
                                matched = False
                                for group_key, group_values in similarity_groups.items():
                                    if (val in group_key or group_key in val or
                                        any(v in val or val in v for v in group_values)):
                                        group_values.append(val)
                                        matched = True
                                        break

                                if not matched:
                                    similarity_groups[val] = [val]

                            # Replace values with group representative (longest string)
                            for group_key, group_values in similarity_groups.items():
                                if len(group_values) > 1:
                                    # Use longest value as canonical form
                                    canonical = max(group_values, key=len)
                                    for val in group_values:
                                        if val != canonical:
                                            cleaned_df[column] = cleaned_df[column].replace(val, canonical)

                                    logger.info(f"Standardized similar values in column '{column}': {group_values} -> {canonical}")
                    except Exception as e:
                        logger.error(f"Error standardizing categorical column '{column}': {e}")

                # Text handling
                elif column_type == 'text':
                    # Strip whitespace
                    if options.get('trim_whitespace', True):
                        try:
                            # Store original nulls
                            null_mask = cleaned_df[column].isna()

                            # Clean string values
                            cleaned_df.loc[~null_mask, column] = (cleaned_df
                                                                .loc[~null_mask, column]
                                                                .astype(str)
                                                                .replace('nan', '')
                                                                .str.strip())
                        except Exception as e:
                            logger.error(f"Error trimming whitespace in column '{column}': {e}")

                    # Apply text normalization if requested
                    if options.get('normalize_text', False):
                        try:
                            # Store original nulls
                            null_mask = cleaned_df[column].isna()

                            # Normalize text
                            cleaned_df.loc[~null_mask, column] = cleaned_df.loc[~null_mask, column].apply(normalize_text)
                        except Exception as e:
                            logger.error(f"Error normalizing text in column '{column}': {e}")

            except Exception as e:
                logger.error(f"Error processing column '{column}': {e}")
                continue

        # Step 5: Handle remaining NaN values
        initial_nulls = cleaned_df.isna().sum().sum()

        # Fill NaN values based on data type
        if options.get('fill_numerics', True):
            try:
                # For numeric columns, fill with 0
                numeric_cols = cleaned_df.select_dtypes(include=['number']).columns
                for col in numeric_cols:
                    try:
                        na_count = cleaned_df[col].isna().sum()
                        if na_count > 0:
                            logger.info(f"Filling {na_count} NaN values in numeric column '{col}' with 0")
                            cleaned_df[col] = cleaned_df[col].fillna(0)
                    except Exception as e:
                        logger.error(f"Error filling NaN in numeric column '{col}': {e}")

                # For string columns, fill with empty string
                string_cols = cleaned_df.select_dtypes(include=['object']).columns
                for col in string_cols:
                    try:
                        na_count = cleaned_df[col].isna().sum()
                        if na_count > 0:
                            logger.info(f"Filling {na_count} NaN values in string column '{col}' with empty string")
                            cleaned_df[col] = cleaned_df[col].fillna('')
                    except Exception as e:
                        logger.error(f"Error filling NaN in string column '{col}': {e}")

                # For date columns, leave as NaT
                # For boolean columns, fill with False
                bool_cols = cleaned_df.select_dtypes(include=['boolean']).columns
                for col in bool_cols:
                    try:
                        na_count = cleaned_df[col].isna().sum()
                        if na_count > 0:
                            logger.info(f"Filling {na_count} NaN values in boolean column '{col}' with False")
                            cleaned_df[col] = cleaned_df[col].fillna(False)
                    except Exception as e:
                        logger.error(f"Error filling NaN in boolean column '{col}': {e}")
            except Exception as e:
                logger.error(f"Error filling NaN values: {e}")

        # Calculate how many missing values were filled
        final_nulls = cleaned_df.isna().sum().sum()
        stats['missing_values_filled'] += (initial_nulls - final_nulls)

    except Exception as e:
        logger.error(f"Error during data cleaning: {e}", exc_info=True)
        # Return original DataFrame if cleaning fails
        return df, stats

    # Complete stats
    stats['cleaned_rows'] = len(cleaned_df)
    stats['percent_reduced'] = round(((stats['original_rows'] - stats['cleaned_rows']) / stats['original_rows']) * 100, 2) if stats['original_rows'] > 0 else 0
    stats['cleaning_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f"Data cleaning complete. Final DataFrame has {len(cleaned_df)} rows")
    logger.info(f"Cleaning statistics: {stats}")
    return cleaned_df, stats

# Improved cleaning algorithm: 2025-04-17 20:28:33

# Improved cleaning algorithm: 2025-04-17 20:28:35

# Improved cleaning algorithm: 2025-04-17 20:28:35

# Improved cleaning algorithm: 2025-04-17 20:28:37

# Improved cleaning algorithm: 2025-04-17 20:28:37

# Improved cleaning algorithm: 2025-04-17 20:28:38

# Improved cleaning algorithm: 2025-04-17 20:28:38

# Improved cleaning algorithm: 2025-04-17 20:28:39

# Improved cleaning algorithm: 2025-04-17 20:28:40

# Improved cleaning algorithm: 2025-04-17 20:28:41

# Improved cleaning algorithm: 2025-04-17 20:28:41

# Improved cleaning algorithm: 2025-04-17 20:28:45

# Improved cleaning algorithm: 2025-04-17 20:28:46

# Improved cleaning algorithm: 2025-04-17 20:28:48

# Improved cleaning algorithm: 2025-04-17 20:28:56

# Improved cleaning algorithm: 2025-04-17 20:28:57

# Improved cleaning algorithm: 2025-04-17 20:28:58

# Improved cleaning algorithm: 2025-04-17 20:28:58

# Improved cleaning algorithm: 2025-04-17 20:28:58

# Improved cleaning algorithm: 2025-04-17 20:29:00

# Improved cleaning algorithm: 2025-04-17 20:29:00

# Improved cleaning algorithm: 2025-04-17 20:29:01

# Improved cleaning algorithm: 2025-04-17 20:29:02

# Improved cleaning algorithm: 2025-04-17 20:29:04

# Improved cleaning algorithm: 2025-04-17 20:29:04

# Improved cleaning algorithm: 2025-04-17 20:29:06

# Improved cleaning algorithm: 2025-04-17 20:29:08

# Improved cleaning algorithm: 2025-04-17 20:29:08

# Improved cleaning algorithm: 2025-04-17 20:29:09

# Improved cleaning algorithm: 2025-04-17 20:29:10

# Improved cleaning algorithm: 2025-04-17 20:29:11

# Improved cleaning algorithm: 2025-04-17 20:29:12

# Improved cleaning algorithm: 2025-04-17 20:29:14

# Improved cleaning algorithm: 2025-04-17 20:29:15

# Improved cleaning algorithm: 2025-04-17 20:29:18

# Improved cleaning algorithm: 2025-04-17 20:29:18

# Improved cleaning algorithm: 2025-04-17 20:29:19

# Improved cleaning algorithm: 2025-04-17 20:29:20

# Improved cleaning algorithm: 2025-04-17 20:29:21

# Improved cleaning algorithm: 2025-04-17 20:29:22

# Improved cleaning algorithm: 2025-04-17 20:29:23

# Improved cleaning algorithm: 2025-04-17 20:29:24

# Improved cleaning algorithm: 2025-04-17 20:29:27

# Improved cleaning algorithm: 2025-04-17 20:29:29

# Improved cleaning algorithm: 2025-04-17 20:29:30

# Improved cleaning algorithm: 2025-04-17 20:29:46

# Improved cleaning algorithm: 2025-04-17 20:29:46

# Improved cleaning algorithm: 2025-04-17 20:29:47

# Improved cleaning algorithm: 2025-04-17 20:29:47

# Improved cleaning algorithm: 2025-04-17 20:29:48

# Improved cleaning algorithm: 2025-04-17 20:30:16

# Improved cleaning algorithm: 2025-04-17 20:30:17

# Improved cleaning algorithm: 2025-04-17 20:30:17

# Improved cleaning algorithm: 2025-04-17 20:30:18

# Improved cleaning algorithm: 2025-04-17 20:30:21

# Improved cleaning algorithm: 2025-04-17 20:30:22

# Improved cleaning algorithm: 2025-04-17 20:30:23

# Improved cleaning algorithm: 2025-04-17 20:30:24

# Improved cleaning algorithm: 2025-04-17 20:30:26

# Improved cleaning algorithm: 2025-04-17 20:30:26

# Improved cleaning algorithm: 2025-04-17 20:30:27

# Improved cleaning algorithm: 2025-04-17 20:30:32

# Improved cleaning algorithm: 2025-04-17 20:30:32

# Improved cleaning algorithm: 2025-04-17 20:30:32

# Improved cleaning algorithm: 2025-04-17 20:30:33

# Improved cleaning algorithm: 2025-04-17 20:30:34

# Improved cleaning algorithm: 2025-04-17 20:30:35

# Improved cleaning algorithm: 2025-04-17 20:30:37

# Improved cleaning algorithm: 2025-04-17 20:30:39

# Improved cleaning algorithm: 2025-04-17 20:30:40

# Improved cleaning algorithm: 2025-04-17 20:30:40

# Improved cleaning algorithm: 2025-04-17 20:30:41

# Improved cleaning algorithm: 2025-04-17 20:30:41

# Improved cleaning algorithm: 2025-04-17 20:30:41

# Improved cleaning algorithm: 2025-04-17 20:30:42

# Improved cleaning algorithm: 2025-04-17 20:30:44

# Improved cleaning algorithm: 2025-04-17 20:30:45

# Improved cleaning algorithm: 2025-04-17 20:30:48

# Improved cleaning algorithm: 2025-04-17 20:30:51

# Improved cleaning algorithm: 2025-04-17 20:30:51

# Improved cleaning algorithm: 2025-04-17 20:30:52

# Improved cleaning algorithm: 2025-04-17 20:30:57

# Improved cleaning algorithm: 2025-04-17 20:30:59

# Improved cleaning algorithm: 2025-04-17 20:31:00

# Improved cleaning algorithm: 2025-04-17 20:31:03

# Improved cleaning algorithm: 2025-04-17 20:31:05

# Improved cleaning algorithm: 2025-04-17 20:31:05

# Improved cleaning algorithm: 2025-04-17 20:31:08

# Improved cleaning algorithm: 2025-04-17 20:31:08

# Improved cleaning algorithm: 2025-04-17 20:31:09

# Improved cleaning algorithm: 2025-04-17 20:31:09

# Improved cleaning algorithm: 2025-04-17 20:31:11

# Improved cleaning algorithm: 2025-04-17 20:31:12

# Improved cleaning algorithm: 2025-04-17 20:31:14

# Improved cleaning algorithm: 2025-04-17 20:31:16

# Improved cleaning algorithm: 2025-04-17 20:31:17

# Improved cleaning algorithm: 2025-04-17 20:31:18

# Improved cleaning algorithm: 2025-04-17 20:31:19

# Improved cleaning algorithm: 2025-04-17 20:31:20

# Improved cleaning algorithm: 2025-04-17 20:31:25

# Improved cleaning algorithm: 2025-04-17 20:31:26

# Improved cleaning algorithm: 2025-04-17 20:31:28

# Improved cleaning algorithm: 2025-04-17 20:31:28

# Improved cleaning algorithm: 2025-04-17 20:31:30

# Improved cleaning algorithm: 2025-04-17 20:31:34

# Improved cleaning algorithm: 2025-04-17 20:31:36

# Improved cleaning algorithm: 2025-04-17 20:31:37

# Improved cleaning algorithm: 2025-04-17 20:31:38

# Improved cleaning algorithm: 2025-04-17 20:31:39

# Improved cleaning algorithm: 2025-04-17 20:31:39

# Improved cleaning algorithm: 2025-04-17 20:31:39

# Improved cleaning algorithm: 2025-04-17 20:31:40

# Improved cleaning algorithm: 2025-04-17 20:31:42

# Improved cleaning algorithm: 2025-04-17 20:31:49

# Improved cleaning algorithm: 2025-04-17 20:31:52

# Improved cleaning algorithm: 2025-04-17 20:31:53

# Improved cleaning algorithm: 2025-04-17 20:31:59

# Improved cleaning algorithm: 2025-04-17 20:31:59

# Improved cleaning algorithm: 2025-04-17 20:31:59

# Improved cleaning algorithm: 2025-04-17 20:32:02

# Improved cleaning algorithm: 2025-04-17 20:32:04

# Improved cleaning algorithm: 2025-04-17 20:32:05

# Improved cleaning algorithm: 2025-04-17 20:32:07

# Improved cleaning algorithm: 2025-04-17 20:32:10

# Improved cleaning algorithm: 2025-04-17 20:32:13

# Improved cleaning algorithm: 2025-04-17 20:32:18

# Improved cleaning algorithm: 2025-04-17 20:32:19

# Improved cleaning algorithm: 2025-04-17 20:32:22

# Improved cleaning algorithm: 2025-04-17 20:32:23

# Improved cleaning algorithm: 2025-04-17 20:32:33

# Improved cleaning algorithm: 2025-04-17 20:32:33

# Improved cleaning algorithm: 2025-04-17 20:32:34

# Improved cleaning algorithm: 2025-04-17 20:57:07
