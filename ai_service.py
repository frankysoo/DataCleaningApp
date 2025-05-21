import os
import json
import requests
import pandas as pd
import logging
import random

logger = logging.getLogger(__name__)

class AICleaningAdvisor:
    """Simulated AI for data cleaning recommendations"""

    def __init__(self, api_key=None):
        """Initialize the AI service"""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        logger.info("Initializing AI Cleaning Advisor (simulation mode)")

    def get_cleaning_recommendations(self, df):
        """
        Get simulated cleaning recommendations based on data analysis

        Args:
            df: pandas DataFrame to analyze

        Returns:
            dict: Recommended cleaning operations with explanations
        """
        try:
            # Prepare data profile for analysis
            data_profile = self._create_data_profile(df)

            # Generate recommendations based on data profile
            recommendations = self._generate_recommendations(data_profile, df)

            logger.info("Generated AI recommendations successfully")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}", exc_info=True)
            return None

    def _create_data_profile(self, df):
        """Create a concise profile of the dataset for the AI"""
        profile = {
            "dataset_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "missing_values_percentage": df.isnull().mean().to_dict(),
                "duplicate_rows_percentage": (1 - df.drop_duplicates().shape[0] / df.shape[0]) * 100
            },
            "column_samples": {},
            "column_types": {}
        }

        # Add sample values and detected types for each column
        for column in df.columns:
            # Get non-null sample values
            non_null_values = df[column].dropna()
            if len(non_null_values) > 0:
                # Take up to 5 sample values
                samples = non_null_values.sample(min(5, len(non_null_values))).tolist()
                # Convert any non-serializable types to strings
                samples = [str(s) if not isinstance(s, (int, float, str, bool)) else s for s in samples]
                profile["column_samples"][column] = samples

                # Detect column type
                if pd.api.types.is_numeric_dtype(df[column]):
                    profile["column_types"][column] = "numeric"
                elif pd.api.types.is_datetime64_dtype(df[column]):
                    profile["column_types"][column] = "datetime"
                else:
                    profile["column_types"][column] = "text"

        return profile

    def _create_ai_prompt(self, data_profile):
        """Create a prompt for the AI model"""
        prompt = f"""
        You are an expert data scientist specializing in data cleaning and preparation.

        I have a dataset with the following characteristics:
        - {data_profile['dataset_info']['rows']} rows and {data_profile['dataset_info']['columns']} columns
        - Column names: {', '.join(data_profile['dataset_info']['column_names'])}
        - Overall missing values: {sum(data_profile['dataset_info']['missing_values_percentage'].values())/len(data_profile['dataset_info']['column_names']):.2f}%
        - Duplicate rows: {data_profile['dataset_info']['duplicate_rows_percentage']:.2f}%

        Here are sample values from each column:

        """

        # Add sample values for each column
        for column, samples in data_profile['column_samples'].items():
            col_type = data_profile['column_types'].get(column, "unknown")
            missing_pct = data_profile['dataset_info']['missing_values_percentage'].get(column, 0) * 100
            prompt += f"Column '{column}' (type: {col_type}, missing: {missing_pct:.1f}%): {samples}\n"

        prompt += """
        Based on this information, please recommend data cleaning operations that should be applied to this dataset.

        For each recommendation, provide:
        1. The specific cleaning operation
        2. Which columns it should be applied to
        3. Why you're recommending it
        4. A confidence level (high, medium, or low)

        Return your response in the following JSON format:
        {
            "recommendations": [
                {
                    "operation": "operation_name",
                    "columns": ["column1", "column2"],
                    "reasoning": "explanation for recommendation",
                    "confidence": "high|medium|low"
                }
            ],
            "summary": "brief summary of overall data quality and recommendations"
        }

        The operation_name should be one of: removeNulls, removeDuplicates, fixDates, standardizeText, fillNumerics, trimWhitespace, fixPhoneNumbers, fixEmails, fixBooleanValues, extractNumericFromText, normalizeText

        Only include operations that you're confident would be beneficial based on the data profile.
        """

        return prompt

    def _generate_recommendations(self, data_profile, df):
        """Generate intelligent cleaning recommendations based on data analysis"""
        # Initialize recommendations structure
        result = {
            "operations": {},
            "confidence": {},
            "reasoning": {},
            "column_specific": {},
            "summary": "Based on analysis of your data, we recommend the following cleaning operations to improve data quality."
        }

        # Check for null values
        null_percentage = df.isnull().mean().mean() * 100
        if null_percentage > 0:
            result["operations"]["removeNulls"] = True
            result["confidence"]["removeNulls"] = min(0.9, null_percentage / 10)
            result["reasoning"]["removeNulls"] = f"Found {null_percentage:.1f}% null values across the dataset"

        # Check for duplicates
        duplicate_percentage = (1 - df.drop_duplicates().shape[0] / df.shape[0]) * 100
        if duplicate_percentage > 0:
            result["operations"]["removeDuplicates"] = True
            result["confidence"]["removeDuplicates"] = min(0.9, duplicate_percentage / 5)
            result["reasoning"]["removeDuplicates"] = f"Found {duplicate_percentage:.1f}% duplicate rows"

        # Analyze columns for specific cleaning needs
        date_columns = []
        phone_columns = []
        email_columns = []
        numeric_text_columns = []
        boolean_columns = []

        for column, samples in data_profile["column_samples"].items():
            # Skip columns with no samples
            if not samples:
                continue

            # Check for date-like columns
            if self._looks_like_date(samples):
                date_columns.append(column)
                if column not in result["column_specific"]:
                    result["column_specific"][column] = {}
                result["column_specific"][column]["fixDates"] = {
                    "recommended": True,
                    "confidence": 0.9,
                    "reasoning": f"Column '{column}' contains date-like values that could be standardized"
                }

            # Check for phone-like columns
            if self._looks_like_phone(samples):
                phone_columns.append(column)
                if column not in result["column_specific"]:
                    result["column_specific"][column] = {}
                result["column_specific"][column]["fixPhoneNumbers"] = {
                    "recommended": True,
                    "confidence": 0.8,
                    "reasoning": f"Column '{column}' contains phone number formats that could be standardized"
                }

            # Check for email-like columns
            if self._looks_like_email(samples):
                email_columns.append(column)
                if column not in result["column_specific"]:
                    result["column_specific"][column] = {}
                result["column_specific"][column]["fixEmails"] = {
                    "recommended": True,
                    "confidence": 0.9,
                    "reasoning": f"Column '{column}' contains email addresses that could be validated and standardized"
                }

            # Check for numeric values in text
            if self._looks_like_numeric_text(samples):
                numeric_text_columns.append(column)
                if column not in result["column_specific"]:
                    result["column_specific"][column] = {}
                result["column_specific"][column]["extractNumericFromText"] = {
                    "recommended": True,
                    "confidence": 0.8,
                    "reasoning": f"Column '{column}' contains numeric values embedded in text (like currency)"
                }

            # Check for boolean-like values
            if self._looks_like_boolean(samples):
                boolean_columns.append(column)
                if column not in result["column_specific"]:
                    result["column_specific"][column] = {}
                result["column_specific"][column]["fixBooleanValues"] = {
                    "recommended": True,
                    "confidence": 0.9,
                    "reasoning": f"Column '{column}' contains boolean-like values that could be standardized"
                }

        # Add general recommendations based on column-specific findings
        if date_columns:
            result["operations"]["fixDates"] = True
            result["confidence"]["fixDates"] = 0.9
            result["reasoning"]["fixDates"] = f"Found {len(date_columns)} columns with date-like values: {', '.join(date_columns[:3])}" + ("..." if len(date_columns) > 3 else "")

        if phone_columns:
            result["operations"]["fixPhoneNumbers"] = True
            result["confidence"]["fixPhoneNumbers"] = 0.8
            result["reasoning"]["fixPhoneNumbers"] = f"Found {len(phone_columns)} columns with phone number formats: {', '.join(phone_columns[:3])}" + ("..." if len(phone_columns) > 3 else "")

        if email_columns:
            result["operations"]["fixEmails"] = True
            result["confidence"]["fixEmails"] = 0.9
            result["reasoning"]["fixEmails"] = f"Found {len(email_columns)} columns with email addresses: {', '.join(email_columns[:3])}" + ("..." if len(email_columns) > 3 else "")

        if numeric_text_columns:
            result["operations"]["extractNumericFromText"] = True
            result["confidence"]["extractNumericFromText"] = 0.8
            result["reasoning"]["extractNumericFromText"] = f"Found {len(numeric_text_columns)} columns with numeric values in text: {', '.join(numeric_text_columns[:3])}" + ("..." if len(numeric_text_columns) > 3 else "")

        if boolean_columns:
            result["operations"]["fixBooleanValues"] = True
            result["confidence"]["fixBooleanValues"] = 0.9
            result["reasoning"]["fixBooleanValues"] = f"Found {len(boolean_columns)} columns with boolean-like values: {', '.join(boolean_columns[:3])}" + ("..." if len(boolean_columns) > 3 else "")

        # Always recommend these common operations
        result["operations"]["standardizeText"] = True
        result["confidence"]["standardizeText"] = 0.7
        result["reasoning"]["standardizeText"] = "Standardizing text case and format improves consistency"

        result["operations"]["trimWhitespace"] = True
        result["confidence"]["trimWhitespace"] = 0.8
        result["reasoning"]["trimWhitespace"] = "Removing extra whitespace improves data quality"

        result["operations"]["fillNumerics"] = True
        result["confidence"]["fillNumerics"] = 0.7
        result["reasoning"]["fillNumerics"] = "Filling missing numeric values with appropriate defaults improves analysis"

        return result

    def _looks_like_date(self, samples):
        """Check if samples look like dates"""
        date_patterns = [
            r'\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}',  # YYYY-MM-DD, MM/DD/YYYY, etc.
            r'\d{1,2}[-/\s][A-Za-z]{3,9}[-/\s]\d{2,4}',  # DD Mon YYYY, etc.
            r'\d{4}',  # Just a year
        ]

        matches = 0
        for sample in samples:
            if not isinstance(sample, str):
                continue

            for pattern in date_patterns:
                if any(c.isdigit() for c in sample) and ('/' in sample or '-' in sample or '.' in sample):
                    matches += 1
                    break

        return matches > 0

    def _looks_like_phone(self, samples):
        """Check if samples look like phone numbers"""
        phone_patterns = [
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\+\d{1,3}\s?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 123-456-7890
        ]

        matches = 0
        for sample in samples:
            if not isinstance(sample, str):
                continue

            if any(c.isdigit() for c in sample) and any(c in sample for c in '()-+.'):
                matches += 1

        return matches > 0

    def _looks_like_email(self, samples):
        """Check if samples look like emails"""
        matches = 0
        for sample in samples:
            if not isinstance(sample, str):
                continue

            if '@' in sample and '.' in sample:
                matches += 1

        return matches > 0

    def _looks_like_numeric_text(self, samples):
        """Check if samples look like numeric values embedded in text"""
        matches = 0
        for sample in samples:
            if not isinstance(sample, str):
                continue

            if any(c.isdigit() for c in sample) and any(c in sample for c in '$€£¥%'):
                matches += 1

        return matches > 0

    def _looks_like_boolean(self, samples):
        """Check if samples look like boolean values"""
        boolean_values = {'yes', 'no', 'true', 'false', 'y', 'n', 't', 'f', '1', '0', 'on', 'off'}

        matches = 0
        for sample in samples:
            if not isinstance(sample, str):
                if sample in (0, 1, True, False):
                    matches += 1
                continue

            if sample.lower() in boolean_values:
                matches += 1

        return matches > 0
