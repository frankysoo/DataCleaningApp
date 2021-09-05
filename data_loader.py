import pandas as pd
import os
import logging
import chardet
import csv
import numpy as np
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def detect_delimiter(filepath, sample_size=10000):
    """
    Detect the delimiter used in a CSV file

    Args:
        filepath: Path to the CSV file
        sample_size: Number of bytes to sample from the file

    Returns:
        Detected delimiter or comma as default
    """
    try:
        with open(filepath, 'rb') as f:
            sample = f.read(sample_size).decode('utf-8', errors='ignore')

        # Count the occurrences of potential delimiters
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample.count(d) for d in delimiters}

        # Find the delimiter with the most occurrences
        max_delimiter = max(counts, key=counts.get)

        # Only return if the delimiter appears at least 5 times
        if counts[max_delimiter] >= 5:
            logger.info(f"Detected delimiter '{max_delimiter}' in {filepath}")
            return max_delimiter
        else:
            logger.info(f"No clear delimiter detected in {filepath}. Using comma as default.")
            return ','
    except Exception as e:
        logger.error(f"Error detecting delimiter: {e}")
        return ','

def inspect_file_headers(filepath, encoding='utf-8'):
    """
    Inspect file headers to help with parsing complex files

    Args:
        filepath: Path to the file
        encoding: Encoding to use for reading the file

    Returns:
        Dictionary with file metadata or None on error
    """
    try:
        file_extension = os.path.splitext(filepath)[1].lower()

        if file_extension == '.csv':
            # For CSV files, try to detect delimiter and check first few rows
            delimiter = detect_delimiter(filepath)

            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                # Read first 10 lines maximum
                lines = [next(f) for _ in range(10) if f]

            # Try to parse with csv module
            sniffer = csv.Sniffer()
            try:
                has_header = sniffer.has_header('\n'.join(lines[:5]))
            except:
                has_header = True  # Assume header exists on error

            return {
                'has_header': has_header,
                'delimiter': delimiter,
                'encoding': encoding,
                'sample_lines': lines
            }

        elif file_extension in ['.xlsx', '.xls']:
            # For Excel files, get sheet names
            try:
                xls = pd.ExcelFile(filepath)
                sheet_names = xls.sheet_names

                # Read first sheet to get column info
                df_sample = pd.read_excel(filepath, sheet_name=sheet_names[0], nrows=5)

                return {
                    'sheet_names': sheet_names,
                    'num_columns': len(df_sample.columns),
                    'column_names': df_sample.columns.tolist(),
                    'num_sheets': len(sheet_names)
                }
            except Exception as e:
                logger.error(f"Error inspecting Excel file: {e}")
                return None

        return None
    except Exception as e:
        logger.error(f"Error inspecting file headers: {e}")
        return None

def load_csv_file(filepath, chunk_size=None):
    """
    Smart loading of CSV files with auto-detection of encoding and delimiters

    Args:
        filepath: Path to the CSV file
        chunk_size: Number of rows to read at a time (for large files)

    Returns:
        Pandas DataFrame or None if loading failed
    """
    try:
        # Detect encoding
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10000 bytes to detect encoding
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
            confidence = detected['confidence']

        logger.info(f"Detected encoding for {filepath}: {encoding} (confidence: {confidence:.2f})")

        # Detect delimiter
        delimiter = detect_delimiter(filepath)

        # Try to read with detected parameters
        try:
            # Check if we should use chunked processing for large files
            file_size = os.path.getsize(filepath)
            use_chunks = chunk_size is not None or file_size > 50 * 1024 * 1024  # Auto-chunk for files > 50MB

            if use_chunks:
                logger.info(f"Using chunked processing for large file: {filepath} ({file_size/1024/1024:.2f} MB)")
                chunk_size = chunk_size or 100000  # Default to 100,000 rows per chunk

                # Use chunked reading for large files
                chunks = []
                try:
                    # Try with on_bad_lines='skip' (pandas >= 1.3.0)
                    for chunk in pd.read_csv(filepath, encoding=encoding, delimiter=delimiter,
                                           on_bad_lines='skip', low_memory=True, chunksize=chunk_size):
                        chunks.append(chunk)
                except TypeError:
                    # Fallback for older pandas versions
                    for chunk in pd.read_csv(filepath, encoding=encoding, delimiter=delimiter,
                                           error_bad_lines=False, low_memory=True, chunksize=chunk_size):
                        chunks.append(chunk)

                if chunks:
                    logger.info(f"Successfully read {len(chunks)} chunks from {filepath}")
                    return pd.concat(chunks, ignore_index=True)
                else:
                    logger.warning(f"No data chunks were read from {filepath}")
                    return None
            else:
                # For smaller files, read all at once
                try:
                    df = pd.read_csv(filepath, encoding=encoding, delimiter=delimiter,
                                    on_bad_lines='skip', low_memory=False)
                except TypeError:
                    # Fallback for older pandas versions
                    df = pd.read_csv(filepath, encoding=encoding, delimiter=delimiter,
                                    error_bad_lines=False, low_memory=False)
                return df
        except Exception as e1:
            logger.warning(f"Failed to read with detected parameters: {e1}")

            # Try alternative encodings
            for enc in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                if enc != encoding:
                    try:
                        logger.info(f"Trying encoding {enc} with delimiter {delimiter}")
                        try:
                            df = pd.read_csv(filepath, encoding=enc, delimiter=delimiter,
                                            on_bad_lines='skip', low_memory=False)
                        except TypeError:
                            df = pd.read_csv(filepath, encoding=enc, delimiter=delimiter,
                                            error_bad_lines=False, low_memory=False)
                        return df
                    except Exception as e:
                        logger.warning(f"Failed with encoding {enc}: {e}")
                        pass

            # Try alternative delimiters
            for delim in [',', ';', '\t', '|']:
                if delim != delimiter:
                    try:
                        logger.info(f"Trying delimiter {delim} with encoding {encoding}")
                        try:
                            df = pd.read_csv(filepath, encoding=encoding, delimiter=delim,
                                            on_bad_lines='skip', low_memory=False)
                        except TypeError:
                            df = pd.read_csv(filepath, encoding=encoding, delimiter=delim,
                                            error_bad_lines=False, low_memory=False)
                        return df
                    except Exception as e:
                        logger.warning(f"Failed with delimiter {delim}: {e}")
                        pass

            # Last resort: try to read with most permissive settings
            try:
                logger.info("Trying most permissive settings (skipping bad lines)")
                try:
                    # Try with pandas engine first
                    df = pd.read_csv(filepath, encoding='latin1', delimiter=',',
                                    on_bad_lines='skip', low_memory=False, engine='python')
                except TypeError:
                    # Fallback for older pandas versions
                    df = pd.read_csv(filepath, encoding='latin1', delimiter=',',
                                    error_bad_lines=False, low_memory=False, engine='python')
                return df
            except Exception as e2:
                logger.error(f"All attempts to read CSV file failed: {e2}")
                # Try one last approach - read as plain text and parse manually
                try:
                    logger.info("Attempting to read file as plain text")
                    with open(filepath, 'r', encoding='latin1', errors='replace') as f:
                        lines = f.readlines()

                    if lines:
                        # Try to split by common delimiters
                        for delim in [',', ';', '\t', '|']:
                            if delim in lines[0]:
                                headers = lines[0].strip().split(delim)
                                data = []
                                for line in lines[1:]:
                                    if line.strip():  # Skip empty lines
                                        values = line.strip().split(delim)
                                        # Pad with None if needed
                                        while len(values) < len(headers):
                                            values.append(None)
                                        data.append(values[:len(headers)])  # Truncate if too long

                                return pd.DataFrame(data, columns=headers)

                    return None
                except Exception as e3:
                    logger.error(f"Manual parsing failed: {e3}")
                    return None
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        return None

def load_excel_file(filepath, chunk_size=None):
    """
    Smart loading of Excel files with fallback engines

    Args:
        filepath: Path to the Excel file
        chunk_size: Number of rows to read at a time (for large files)

    Returns:
        Pandas DataFrame or None if loading failed
    """
    try:
        # Try openpyxl engine first (better for newer Excel files)
        try:
            xls = pd.ExcelFile(filepath, engine='openpyxl')
            sheet_names = xls.sheet_names

            # Check file size to determine if we need chunked processing
            file_size = os.path.getsize(filepath)
            use_chunks = chunk_size is not None or file_size > 50 * 1024 * 1024  # Auto-chunk for files > 50MB

            # If multiple sheets, load all and concatenate
            if len(sheet_names) > 1:
                logger.info(f"Multiple sheets found ({len(sheet_names)}), loading all")
                all_dfs = []

                for sheet in sheet_names:
                    try:
                        if use_chunks:
                            logger.info(f"Using chunked processing for large Excel file: {filepath}, sheet: {sheet} ({file_size/1024/1024:.2f} MB)")
                            chunk_size = chunk_size or 10000  # Default to 10,000 rows per chunk for Excel

                            # For Excel, we need to read in chunks manually
                            sheet_chunks = []
                            row_start = 0
                            while True:
                                try:
                                    # Read a chunk of rows
                                    chunk = pd.read_excel(filepath, sheet_name=sheet, engine='openpyxl',
                                                        skiprows=row_start, nrows=chunk_size)

                                    if chunk.empty:
                                        break

                                    sheet_chunks.append(chunk)
                                    row_start += len(chunk)

                                    # If we got fewer rows than requested, we've reached the end
                                    if len(chunk) < chunk_size:
                                        break
                                except Exception as chunk_err:
                                    logger.error(f"Error reading chunk from sheet '{sheet}': {chunk_err}")
                                    break

                            if sheet_chunks:
                                sheet_df = pd.concat(sheet_chunks, ignore_index=True)
                                # Add sheet name as column for reference
                                sheet_df['source_sheet'] = sheet
                                all_dfs.append(sheet_df)
                        else:
                            # For smaller files, read the whole sheet at once
                            sheet_df = pd.read_excel(filepath, sheet_name=sheet, engine='openpyxl')
                            if not sheet_df.empty:
                                # Add sheet name as column for reference
                                sheet_df['source_sheet'] = sheet
                                all_dfs.append(sheet_df)
                    except Exception as sheet_err:
                        logger.warning(f"Error loading sheet '{sheet}': {sheet_err}")

                if all_dfs:
                    return pd.concat(all_dfs, ignore_index=True)
                else:
                    logger.warning("No valid sheets found in the Excel file")
                    return None
            else:
                # Single sheet - load directly or in chunks
                if use_chunks:
                    logger.info(f"Using chunked processing for large Excel file: {filepath} ({file_size/1024/1024:.2f} MB)")
                    chunk_size = chunk_size or 10000  # Default to 10,000 rows per chunk for Excel

                    # For Excel, we need to read in chunks manually
                    chunks = []
                    row_start = 0
                    while True:
                        try:
                            # Read a chunk of rows
                            chunk = pd.read_excel(filepath, engine='openpyxl',
                                                skiprows=row_start, nrows=chunk_size)

                            if chunk.empty:
                                break

                            chunks.append(chunk)
                            row_start += len(chunk)

                            # If we got fewer rows than requested, we've reached the end
                            if len(chunk) < chunk_size:
                                break
                        except Exception as chunk_err:
                            logger.error(f"Error reading chunk: {chunk_err}")
                            break

                    if chunks:
                        return pd.concat(chunks, ignore_index=True)
                    else:
                        logger.warning("No data chunks were read from Excel file")
                        return None
                else:
                    # For smaller files, read all at once
                    return pd.read_excel(filepath, engine='openpyxl')

        except Exception as openpyxl_err:
            logger.warning(f"Error with openpyxl engine: {openpyxl_err}. Trying xlrd engine.")

            # Fallback to xlrd engine
            try:
                df = pd.read_excel(filepath, engine='xlrd')
                return df
            except Exception as xlrd_err:
                logger.error(f"All Excel engines failed: {xlrd_err}")
                return None

    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        return None

def load_and_merge_data(file_paths, chunk_size=None):
    """
    Load and merge data from multiple CSV or Excel files with enhanced support
    for complex files and error handling

    Args:
        file_paths: List of file paths to CSV or Excel files

    Returns:
        Merged pandas DataFrame or None if loading failed
    """
    dataframes = []
    file_meta = {}

    if not file_paths:
        logger.error("No file paths provided")
        return None

    for filepath in file_paths:
        logger.info(f"Loading file: {filepath}")
        if not os.path.exists(filepath):
            logger.error(f"File does not exist: {filepath}")
            continue

        # Check if file is empty
        if os.path.getsize(filepath) == 0:
            logger.error(f"File is empty: {filepath}")
            continue

        file_extension = os.path.splitext(filepath)[1].lower()
        logger.info(f"File extension: {file_extension}")

        try:
            # Load based on file type
            if file_extension == '.csv':
                logger.info(f"Loading CSV file: {filepath}")
                df = load_csv_file(filepath, chunk_size=chunk_size)
                if df is None:
                    # Try loading as Excel in case of misnamed file
                    logger.info(f"Trying to load {filepath} as Excel file")
                    df = load_excel_file(filepath, chunk_size=chunk_size)
            elif file_extension in ['.xlsx', '.xls']:
                logger.info(f"Loading Excel file: {filepath}")
                df = load_excel_file(filepath, chunk_size=chunk_size)
                if df is None:
                    # Try loading as CSV in case of misnamed file
                    logger.info(f"Trying to load {filepath} as CSV file")
                    df = load_csv_file(filepath, chunk_size=chunk_size)
            else:
                logger.warning(f"Unsupported file extension: {file_extension}, trying as CSV")
                df = load_csv_file(filepath, chunk_size=chunk_size)
                if df is None:
                    logger.warning(f"Trying as Excel file")
                    df = load_excel_file(filepath, chunk_size=chunk_size)

            # Check if loading was successful
            if df is None:
                logger.warning(f"Failed to load file: {filepath}")
                continue

            # Basic validation and normalization
            if df.shape[1] > 0:
                # Handle dtypes to avoid merge issues
                for col in df.columns:
                    # Convert any problematic types to safe representations
                    # Check for date columns
                    if 'date' in col.lower() or 'time' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col], errors='ignore')
                        except:
                            pass

                # Convert any empty strings to NaN for consistency
                df = df.replace('', pd.NA)

                # Handle duplicate column names by adding suffixes
                if df.columns.duplicated().any():
                    logger.warning(f"Duplicate column names found in {filepath}. Renaming columns.")
                    df.columns = pd.Series(df.columns).astype(str) + '_' + pd.Series(range(len(df.columns))).astype(str)

                # Add source file information as a column
                df['source_file'] = os.path.basename(filepath)
                df['import_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                logger.info(f"Successfully loaded {filepath} with {len(df)} rows and {df.shape[1]} columns")
                dataframes.append(df)

                # Save metadata for post-processing
                file_meta[filepath] = {
                    'rows': len(df),
                    'columns': df.shape[1],
                    'column_names': df.columns.tolist()
                }
            else:
                logger.warning(f"File {filepath} has no columns")

        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}", exc_info=True)
            continue

    if not dataframes:
        logger.warning("No valid data loaded from files")
        return None

    # Merge all dataframes
    try:
        # If only one dataframe, return it directly
        if len(dataframes) == 1:
            logger.info(f"Only one file loaded, returning single DataFrame with {len(dataframes[0])} rows")
            return dataframes[0]

        # Try to find common columns for intelligent merging
        common_cols = set.intersection(*[set(df.columns) for df in dataframes])
        common_cols = [col for col in common_cols if col not in ['source_file', 'import_timestamp']]

        # Use common columns for merging if they exist and are useful
        if len(common_cols) > 0 and len(common_cols) < min(df.shape[1] for df in dataframes):
            logger.info(f"Found {len(common_cols)} common columns across files: {common_cols}")
            # Check if any common column could be a key for joining
            for col in common_cols:
                # Check if column has mostly unique values in each dataframe
                is_potential_key = all(df[col].nunique() / len(df) > 0.8 for df in dataframes if len(df) > 0)

                if is_potential_key:
                    logger.info(f"Column '{col}' identified as potential key for merging")
                    # Try to merge on this column
                    try:
                        result_df = dataframes[0]
                        for i, df in enumerate(dataframes[1:], 1):
                            result_df = pd.merge(result_df, df, on=col, how='outer',
                                               suffixes=(f'_1', f'_{i+1}'))

                        logger.info(f"Successfully merged files using column '{col}'")
                        return result_df
                    except Exception as merge_err:
                        logger.warning(f"Failed to merge on column '{col}': {merge_err}")

        # If intelligent merging failed or wasn't possible, use standard concatenation
        logger.info("Using standard concatenation for merging files")
        merged_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Successfully merged {len(dataframes)} files into a DataFrame with {len(merged_df)} rows")
        return merged_df

    except Exception as e:
        logger.error(f"Error merging dataframes: {e}", exc_info=True)
        if len(dataframes) == 1:
            # If concat fails but we have one dataframe, return it
            logger.info("Returning single dataframe as fallback")
            return dataframes[0]
        return None

# Enhanced data loading: 2025-04-17 20:28:34

# Enhanced data loading: 2025-04-17 20:28:34

# Enhanced data loading: 2025-04-17 20:28:35

# Enhanced data loading: 2025-04-17 20:28:38

# Enhanced data loading: 2025-04-17 20:28:39

# Enhanced data loading: 2025-04-17 20:28:41

# Enhanced data loading: 2025-04-17 20:28:42

# Enhanced data loading: 2025-04-17 20:28:42

# Enhanced data loading: 2025-04-17 20:28:44

# Enhanced data loading: 2025-04-17 20:28:46

# Enhanced data loading: 2025-04-17 20:28:47

# Enhanced data loading: 2025-04-17 20:28:48

# Enhanced data loading: 2025-04-17 20:28:49

# Enhanced data loading: 2025-04-17 20:28:51

# Enhanced data loading: 2025-04-17 20:28:52

# Enhanced data loading: 2025-04-17 20:28:52

# Enhanced data loading: 2025-04-17 20:28:54

# Enhanced data loading: 2025-04-17 20:28:55

# Enhanced data loading: 2025-04-17 20:28:56

# Enhanced data loading: 2025-04-17 20:28:56

# Enhanced data loading: 2025-04-17 20:28:57

# Enhanced data loading: 2025-04-17 20:29:00

# Enhanced data loading: 2025-04-17 20:29:01

# Enhanced data loading: 2025-04-17 20:29:02

# Enhanced data loading: 2025-04-17 20:29:03

# Enhanced data loading: 2025-04-17 20:29:03

# Enhanced data loading: 2025-04-17 20:29:05

# Enhanced data loading: 2025-04-17 20:29:05

# Enhanced data loading: 2025-04-17 20:29:06

# Enhanced data loading: 2025-04-17 20:29:12

# Enhanced data loading: 2025-04-17 20:29:13

# Enhanced data loading: 2025-04-17 20:29:14

# Enhanced data loading: 2025-04-17 20:29:14

# Enhanced data loading: 2025-04-17 20:29:16

# Enhanced data loading: 2025-04-17 20:29:16

# Enhanced data loading: 2025-04-17 20:29:17

# Enhanced data loading: 2025-04-17 20:29:19

# Enhanced data loading: 2025-04-17 20:29:21

# Enhanced data loading: 2025-04-17 20:29:24

# Enhanced data loading: 2025-04-17 20:29:25

# Enhanced data loading: 2025-04-17 20:29:26

# Enhanced data loading: 2025-04-17 20:29:26

# Enhanced data loading: 2025-04-17 20:29:26

# Enhanced data loading: 2025-04-17 20:29:28

# Enhanced data loading: 2025-04-17 20:30:18

# Enhanced data loading: 2025-04-17 20:30:18

# Enhanced data loading: 2025-04-17 20:30:19

# Enhanced data loading: 2025-04-17 20:30:20

# Enhanced data loading: 2025-04-17 20:30:21

# Enhanced data loading: 2025-04-17 20:30:24

# Enhanced data loading: 2025-04-17 20:30:27

# Enhanced data loading: 2025-04-17 20:30:28

# Enhanced data loading: 2025-04-17 20:30:29

# Enhanced data loading: 2025-04-17 20:30:29

# Enhanced data loading: 2025-04-17 20:30:30

# Enhanced data loading: 2025-04-17 20:30:30

# Enhanced data loading: 2025-04-17 20:30:30

# Enhanced data loading: 2025-04-17 20:30:34

# Enhanced data loading: 2025-04-17 20:30:36

# Enhanced data loading: 2025-04-17 20:30:36

# Enhanced data loading: 2025-04-17 20:30:38

# Enhanced data loading: 2025-04-17 20:30:39

# Enhanced data loading: 2025-04-17 20:30:42

# Enhanced data loading: 2025-04-17 20:30:43

# Enhanced data loading: 2025-04-17 20:30:45

# Enhanced data loading: 2025-04-17 20:30:46

# Enhanced data loading: 2025-04-17 20:30:46

# Enhanced data loading: 2025-04-17 20:30:47

# Enhanced data loading: 2025-04-17 20:30:47

# Enhanced data loading: 2025-04-17 20:30:48

# Enhanced data loading: 2025-04-17 20:30:51

# Enhanced data loading: 2025-04-17 20:30:53

# Enhanced data loading: 2025-04-17 20:30:54

# Enhanced data loading: 2025-04-17 20:30:54

# Enhanced data loading: 2025-04-17 20:30:55

# Enhanced data loading: 2025-04-17 20:30:55

# Enhanced data loading: 2025-04-17 20:30:58

# Enhanced data loading: 2025-04-17 20:30:58

# Enhanced data loading: 2025-04-17 20:31:01

# Enhanced data loading: 2025-04-17 20:31:02

# Enhanced data loading: 2025-04-17 20:31:04

# Enhanced data loading: 2025-04-17 20:31:07

# Enhanced data loading: 2025-04-17 20:31:12

# Enhanced data loading: 2025-04-17 20:31:13

# Enhanced data loading: 2025-04-17 20:31:13

# Enhanced data loading: 2025-04-17 20:31:13

# Enhanced data loading: 2025-04-17 20:31:15

# Enhanced data loading: 2025-04-17 20:31:17

# Enhanced data loading: 2025-04-17 20:31:19

# Enhanced data loading: 2025-04-17 20:31:19

# Enhanced data loading: 2025-04-17 20:31:20

# Enhanced data loading: 2025-04-17 20:31:23

# Enhanced data loading: 2025-04-17 20:31:24

# Enhanced data loading: 2025-04-17 20:31:25

# Enhanced data loading: 2025-04-17 20:31:26

# Enhanced data loading: 2025-04-17 20:31:27

# Enhanced data loading: 2025-04-17 20:31:30

# Enhanced data loading: 2025-04-17 20:31:31

# Enhanced data loading: 2025-04-17 20:31:33

# Enhanced data loading: 2025-04-17 20:31:34

# Enhanced data loading: 2025-04-17 20:31:35

# Enhanced data loading: 2025-04-17 20:31:36

# Enhanced data loading: 2025-04-17 20:31:38

# Enhanced data loading: 2025-04-17 20:31:43

# Enhanced data loading: 2025-04-17 20:31:43

# Enhanced data loading: 2025-04-17 20:31:44

# Enhanced data loading: 2025-04-17 20:31:44

# Enhanced data loading: 2025-04-17 20:31:45

# Enhanced data loading: 2025-04-17 20:31:46

# Enhanced data loading: 2025-04-17 20:31:48

# Enhanced data loading: 2025-04-17 20:31:52

# Enhanced data loading: 2025-04-17 20:31:56

# Enhanced data loading: 2025-04-17 20:31:57

# Enhanced data loading: 2025-04-17 20:32:00

# Enhanced data loading: 2025-04-17 20:32:06

# Enhanced data loading: 2025-04-17 20:32:07

# Enhanced data loading: 2025-04-17 20:32:08

# Enhanced data loading: 2025-04-17 20:32:09

# Enhanced data loading: 2025-04-17 20:32:09

# Enhanced data loading: 2025-04-17 20:32:10

# Enhanced data loading: 2025-04-17 20:32:12

# Enhanced data loading: 2025-04-17 20:32:14

# Enhanced data loading: 2025-04-17 20:32:15

# Enhanced data loading: 2025-04-17 20:32:20

# Enhanced data loading: 2025-04-17 20:32:22

# Enhanced data loading: 2025-04-17 20:32:23

# Enhanced data loading: 2025-04-17 20:32:23

# Enhanced data loading: 2025-04-17 20:32:25

# Enhanced data loading: 2025-04-17 20:32:26

# Enhanced data loading: 2025-04-17 20:32:27

# Enhanced data loading: 2025-04-17 20:32:28

# Enhanced data loading: 2025-04-17 20:32:28

# Enhanced data loading: 2025-04-17 20:32:31

# Enhanced data loading: 2025-04-17 20:32:35

# Enhanced data loading: 2025-04-17 20:32:37

# Enhanced data loading: 2025-04-17 20:32:37

# Enhanced data loading: 2025-04-17 20:57:07

# Enhanced data loading: 2025-04-17 20:57:08
