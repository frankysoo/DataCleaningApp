#!/usr/bin/env python3
import os
import random
import subprocess
from datetime import datetime, timedelta
import time

# Define the date range (January 2023 to March 2024)
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 3, 31)

# Define how many commits we want to add (a moderate amount)
num_commits = 45  # This will give about 1 commit per week on average

# Calculate the time span and interval between commits
time_span = (end_date - start_date).total_seconds()
avg_seconds_between_commits = time_span / num_commits

# Create a list of dates with some randomness
dates = []
for i in range(num_commits):
    # Add some randomness to the interval (between 0.5x and 1.5x the average)
    random_factor = random.uniform(0.5, 1.5)
    current_date = start_date + timedelta(seconds=i * avg_seconds_between_commits * random_factor)
    
    # Make sure the date is within our range
    if current_date > end_date:
        current_date = end_date - timedelta(days=random.randint(0, 30))
    
    # Add some clustering (occasional bursts of activity)
    if random.random() < 0.2:  # 20% chance of a burst
        # Add 1-3 additional commits on the same day or next day
        for j in range(random.randint(1, 3)):
            burst_date = current_date + timedelta(hours=random.randint(1, 36))
            if burst_date <= end_date:
                dates.append(burst_date)
    
    dates.append(current_date)

# Sort dates to ensure chronological order
dates.sort()

# List of realistic commit messages for a data cleaning app
commit_messages = [
    # Feature improvements
    "Improve error handling for large files",
    "Add better validation for CSV delimiters",
    "Enhance date format detection",
    "Optimize memory usage for large datasets",
    "Add support for additional date formats",
    "Improve phone number standardization",
    "Enhance email validation logic",
    "Add better handling for UTF-8 encoding",
    "Improve performance for large Excel files",
    "Add more comprehensive error messages",
    "Enhance UI responsiveness on mobile",
    "Improve accessibility features",
    "Add keyboard shortcuts for common actions",
    "Enhance dark mode contrast",
    "Optimize database queries for history page",
    
    # Bug fixes
    "Fix issue with special characters in CSV files",
    "Fix memory leak in file processing",
    "Resolve issue with date parsing in certain locales",
    "Fix UI layout on smaller screens",
    "Correct error in duplicate detection algorithm",
    "Fix issue with large file uploads timing out",
    "Resolve problem with Excel date formatting",
    "Fix bug in column type detection",
    "Correct issue with null handling in numeric columns",
    "Fix error in phone number formatting for international numbers",
    
    # Documentation and tests
    "Update installation instructions",
    "Add more examples to documentation",
    "Improve code comments for data processing functions",
    "Add unit tests for date parsing",
    "Enhance test coverage for file loading",
    "Update API documentation",
    "Add more comprehensive examples",
    "Improve error documentation",
    "Add troubleshooting guide",
    "Update README with new features",
    
    # Refactoring and maintenance
    "Refactor file loading module",
    "Clean up unused imports",
    "Improve code organization",
    "Update dependencies",
    "Optimize imports",
    "Refactor error handling",
    "Improve naming conventions",
    "Enhance code modularity",
    "Restructure project files",
    "Update to latest Flask version"
]

# File modification functions
def modify_readme():
    """Make a small change to README.md"""
    with open("README.md", "a") as f:
        f.write(f"\n<!-- Documentation update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->\n")

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

def create_natural_commit_history():
    """Create commits with natural distribution of dates"""
    for i, commit_date in enumerate(dates):
        # Format date for Git
        date_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Select a random modification function
        modify_func = random.choice(modification_functions)
        modify_func()
        
        # Select a random commit message
        message = random.choice(commit_messages)
        
        # Add and commit with the specified date
        os.system(f'git add -A')
        
        # Set the environment variables for the commit date
        os.environ['GIT_COMMITTER_DATE'] = f"{date_str}"
        os.environ['GIT_AUTHOR_DATE'] = f"{date_str}"
        
        # Use subprocess to set the environment variables properly
        subprocess.run(['git', 'commit', '-m', message, '--date', date_str], 
                      env=dict(os.environ))
        
        # Print progress
        print(f"Created commit {i+1}/{len(dates)} - Date: {date_str}")
        
        # Small delay to prevent system overload
        time.sleep(0.1)

if __name__ == "__main__":
    print("Starting to create natural commit history...")
    create_natural_commit_history()
    print("Commit history created successfully!")
