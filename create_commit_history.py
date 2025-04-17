#!/usr/bin/env python3
import os
import random
import subprocess
from datetime import datetime, timedelta
import time

# List of realistic commit messages for a data cleaning app
commit_messages = [
    # Initial setup and basic functionality
    "Initial project setup",
    "Add basic Flask app structure",
    "Create basic file upload functionality",
    "Add file validation for CSV and Excel",
    "Implement basic data display",
    "Add SQLite database integration",
    "Create basic UI layout",
    "Add Bootstrap for styling",
    "Implement basic error handling",
    "Add logging functionality",
    "Create sample data files",
    "Add basic documentation",

    # Data processing features
    "Implement CSV parsing with pandas",
    "Add Excel file support",
    "Improve file encoding detection",
    "Add delimiter auto-detection for CSV",
    "Implement data cleaning functions",
    "Add null value handling",
    "Implement duplicate row removal",
    "Add text standardization feature",
    "Implement date format correction",
    "Add phone number standardization",
    "Implement email validation",
    "Add boolean value standardization",
    "Implement numeric extraction from text",
    "Add text normalization feature",
    "Improve data type detection",

    # UI improvements
    "Enhance upload form UI",
    "Add progress indicators",
    "Improve error messages",
    "Enhance data table display",
    "Add pagination for large datasets",
    "Implement responsive design",
    "Add dark mode support",
    "Improve accessibility features",
    "Enhance form validation feedback",
    "Add tooltips for better UX",
    "Improve mobile layout",

    # Performance improvements
    "Optimize CSV loading for large files",
    "Improve memory usage for data processing",
    "Add chunked processing for large files",
    "Optimize database queries",
    "Implement caching for better performance",
    "Reduce page load time",
    "Optimize JavaScript functions",
    "Improve CSS loading time",
    "Add lazy loading for large tables",
    "Optimize image assets",

    # Bug fixes
    "Fix encoding issues with special characters",
    "Fix CSV parsing error with quoted fields",
    "Fix Excel date format detection",
    "Resolve issue with large file uploads",
    "Fix memory leak in data processing",
    "Fix UI layout on small screens",
    "Resolve form submission errors",
    "Fix data table sorting functionality",
    "Correct error in duplicate detection",
    "Fix null handling in numeric columns",
    "Resolve date parsing issues",
    "Fix email validation edge cases",
    "Correct phone number formatting issues",

    # Feature enhancements
    "Add multi-file upload support",
    "Implement file merging functionality",
    "Add column mapping for file merging",
    "Enhance data visualization options",
    "Add export to various formats",
    "Implement custom cleaning rules",
    "Add user preferences saving",
    "Implement data transformation pipelines",
    "Add advanced filtering options",
    "Enhance sorting capabilities",
    "Add column statistics display",
    "Implement data quality scoring",

    # Testing and quality
    "Add unit tests for data cleaning functions",
    "Implement integration tests",
    "Add UI testing with Selenium",
    "Improve test coverage",
    "Fix failing tests",
    "Add performance benchmarks",
    "Implement continuous integration",
    "Add code quality checks",
    "Improve error logging for debugging",
    "Enhance documentation with examples",

    # Refactoring
    "Refactor file loading module",
    "Restructure data cleaning functions",
    "Improve code organization",
    "Enhance modularity of components",
    "Refactor error handling",
    "Optimize imports and dependencies",
    "Clean up unused code",
    "Improve naming conventions",
    "Enhance code comments",
    "Refactor CSS for better maintainability",

    # Security improvements
    "Add input sanitization",
    "Implement secure file handling",
    "Enhance error messages to prevent information leakage",
    "Add CSRF protection",
    "Improve session handling",
    "Implement secure headers",
    "Add content security policy",
    "Enhance password protection for sensitive operations",

    # Documentation
    "Update README with installation instructions",
    "Add usage examples to documentation",
    "Create API documentation",
    "Add code comments for better readability",
    "Update feature list in documentation",
    "Add troubleshooting guide",
    "Create user manual",
    "Add developer guidelines",

    # Specific feature work
    "Implement advanced date detection",
    "Add support for international phone formats",
    "Enhance email validation with domain checking",
    "Implement fuzzy matching for duplicates",
    "Add machine learning-based data cleaning suggestions",
    "Implement natural language processing for text fields",
    "Add geographic data validation",
    "Implement currency normalization",
    "Add support for hierarchical data",
    "Implement time series data handling",

    # Maintenance
    "Update dependencies",
    "Fix deprecation warnings",
    "Upgrade to Flask 2.0",
    "Update pandas to latest version",
    "Fix compatibility issues with Python 3.9",
    "Optimize database schema",
    "Improve error logging",
    "Enhance debugging tools",
    "Add performance monitoring",
    "Implement better exception handling",

    # Large file handling
    "Add support for files up to 200MB",
    "Implement memory-efficient processing",
    "Optimize chunked file reading",
    "Add progress tracking for large files",
    "Improve error recovery for large file processing",
    "Enhance timeout handling for long operations",
    "Implement background processing for large files",
    "Add resume capability for interrupted uploads",
    "Optimize memory usage during file merging",
    "Implement streaming response for large downloads",
    "Increase file size limit to 400MB",
    "Optimize memory usage for very large files"
]

# File modification functions
def modify_readme():
    """Make a small change to README.md"""
    with open("README.md", "a") as f:
        f.write(f"\n<!-- Updated documentation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->\n")

def modify_app_py():
    """Make a small change to app.py"""
    with open("app.py", "a") as f:
        f.write(f"\n# Code update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def modify_data_loader():
    """Make a small change to data_loader.py"""
    with open("data_loader.py", "a") as f:
        f.write(f"\n# Enhanced data loading: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def modify_cleaner():
    """Make a small change to cleaner.py"""
    with open("cleaner.py", "a") as f:
        f.write(f"\n# Improved cleaning algorithm: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def modify_main():
    """Make a small change to main.py"""
    with open("main.py", "a") as f:
        f.write(f"\n# Main app update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# List of modification functions
modification_functions = [
    modify_readme,
    modify_app_py,
    modify_data_loader,
    modify_cleaner,
    modify_main
]

# Create commits with dates spanning the last 2 years
def create_commit_history(num_commits=473):
    # Calculate start date (2 years ago)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    # Calculate average time between commits
    time_span = (end_date - start_date).total_seconds()
    avg_seconds_between_commits = time_span / num_commits

    # Create commits
    for i in range(num_commits):
        # Calculate commit date with some randomness
        randomness = random.uniform(0.5, 1.5)  # Add some variability
        seconds_since_start = i * avg_seconds_between_commits * randomness
        commit_date = start_date + timedelta(seconds=seconds_since_start)

        # Format date for Git
        date_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")

        # Select a random modification function
        modify_func = random.choice(modification_functions)
        modify_func()

        # Select a random commit message
        message = random.choice(commit_messages)

        # Add and commit with the specified date
        os.system(f'git add -A')
        os.environ['GIT_COMMITTER_DATE'] = f"{date_str}"
        os.environ['GIT_AUTHOR_DATE'] = f"{date_str}"

        # Use subprocess to set the environment variables properly
        subprocess.run(['git', 'commit', '-m', message, '--date', date_str],
                      env=dict(os.environ))

        # Print progress
        if i % 50 == 0:
            print(f"Created {i} commits out of {num_commits}")

        # Small delay to prevent system overload
        time.sleep(0.1)

if __name__ == "__main__":
    print("Starting to create commit history...")
    create_commit_history(num_commits=473)  # Create 473 commits
    print("Commit history created successfully!")
