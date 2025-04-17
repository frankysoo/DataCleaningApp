import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string
import os

# Create directory if it doesn't exist
os.makedirs('sample_files', exist_ok=True)

# Create Employee Sample Data
def create_employee_data():
    np.random.seed(42)
    n = 100
    
    # Create employee data with various inconsistencies
    data = {
        'EmployeeID': np.arange(1, n+1),
        'Name': [f'{random.choice("John Maria Sarah Robert Emma Michael".split())} {random.choice("Smith Johnson Williams Brown Jones Davis".split())}' for _ in range(n)],
        'Email': [f'employee_{i}@example.com' if i % 10 != 0 else f'EMPLOYEE_{i}@EXAMPLE.COM' for i in range(1, n+1)],
        'Phone': [f'+1 ({random.randint(100, 999)})-{random.randint(100, 999)}-{random.randint(1000, 9999)}' if i % 6 != 0 else
                  f'{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(1000, 9999)}' for i in range(n)],
        'Department': [random.choice(['HR', 'IT', 'Sales', 'Marketing', 'Finance', 'Operations']) for _ in range(n)],
        'HireDate': [(datetime.now() - timedelta(days=random.randint(1, 3650))).strftime(random.choice(['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y'])) for _ in range(n)],
        'Salary': [f'${random.randint(30, 150)},{random.randint(0, 999)}' if i % 5 != 0 else random.randint(30000, 150000) for i in range(n)],
        'IsActive': [random.choice(['Yes', 'No', 'TRUE', 'FALSE', '1', '0', 'Y', 'N']) for _ in range(n)],
    }
    
    # Add some NaN values
    for col in data:
        if col != 'EmployeeID':
            for i in range(n):
                if random.random() < 0.05:
                    data[col][i] = np.nan
    
    return pd.DataFrame(data)

# Create Sales Sample Data
def create_sales_data():
    np.random.seed(43)
    n = 150
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    product_categories = ['Electronics', 'Clothing', 'Books', 'Home & Kitchen', 'Sports', 'Beauty']
    product_names = {
        'Electronics': ['Smartphone', 'Laptop', 'Headphones', 'Tablet', 'Camera'],
        'Clothing': ['T-shirt', 'Jeans', 'Dress', 'Jacket', 'Shoes'],
        'Books': ['Fiction', 'Non-fiction', 'Biography', 'Textbook', "Children's"],
        'Home & Kitchen': ['Blender', 'Coffee Maker', 'Toaster', 'Microwave', 'Vacuum Cleaner'],
        'Sports': ['Yoga Mat', 'Dumbbells', 'Tennis Racket', 'Basketball', 'Running Shoes'],
        'Beauty': ['Shampoo', 'Moisturizer', 'Makeup Kit', 'Perfume', 'Hairdryer']
    }
    
    data = {
        'OrderID': np.arange(1001, 1001+n),
        'Date': [(start_date + timedelta(days=random.randint(0, (end_date - start_date).days))).strftime(random.choice(['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y'])) for _ in range(n)],
        'CustomerID': [random.randint(1, 500) for _ in range(n)],
        'Category': [random.choice(product_categories) for _ in range(n)],
        'PaymentMethod': [random.choice(['Credit Card', 'PayPal', 'Cash', 'Bank Transfer', 'Check']) for _ in range(n)],
        'ShippingStatus': [random.choice(['Delivered', 'Pending', 'Shipped', 'CANCELLED', 'Returned']) for _ in range(n)],
    }
    
    # Add product based on category
    products = []
    for cat in data['Category']:
        products.append(random.choice(product_names[cat]))
    data['Product'] = products
    
    # Add prices with currency formatting issues
    prices = []
    for i in range(n):
        price = random.uniform(10, 2000)
        if i % 10 == 0:
            prices.append(f'${price:.2f}')
        elif i % 7 == 0:
            prices.append(f'€{price:.2f}'.replace('.', ','))
        elif i % 5 == 0:
            prices.append(f'{price:.2f} USD')
        else:
            prices.append(price)
    data['Price'] = prices
    
    # Add quantities
    data['Quantity'] = [random.randint(1, 10) for _ in range(n)]
    
    # Add some NaN values
    for col in data:
        if col not in ['OrderID', 'Date', 'Price']:
            for i in range(n):
                if random.random() < 0.05:
                    data[col][i] = np.nan
    
    return pd.DataFrame(data)

# Create Malformed Data
def create_malformed_data():
    np.random.seed(45)
    n = 50
    
    # Create a dataframe with intentional issues
    data = pd.DataFrame({
        'ID': list(range(1, n+1)),
        'Text_With_Nulls': [random.choice(['Some text', '', np.nan, None]) for _ in range(n)],
        'Mixed_Types': [random.choice([random.randint(1, 100), f'String-{random.randint(1, 100)}', random.random()]) for _ in range(n)],
        'Inconsistent_Dates': [random.choice([datetime.now().strftime('%Y-%m-%d'), 
                                           datetime.now().strftime('%m/%d/%Y'),
                                           datetime.now().strftime('%d-%b-%Y'),
                                           'Not a date',
                                           np.nan]) for _ in range(n)],
        'Duplicated_Column': [random.randint(1, 10) for _ in range(n)],
        'Another_Duplicated_Column': [random.randint(1, 10) for _ in range(n)],
    })
    
    # Add a couple of completely duplicate rows
    for i in range(5):
        duplicate_index = random.randint(0, n-1)
        data.loc[n+i] = data.loc[duplicate_index]
    
    return data

def main():
    print("Creating sample files...")
    
    # Generate datasets
    employee_df = create_employee_data()
    sales_df = create_sales_data()
    malformed_df = create_malformed_data()
    
    # Save to Excel files
    employee_df.to_excel('sample_files/employee_data.xlsx', index=False)
    sales_df.to_excel('sample_files/sales_data.xlsx', index=False)
    malformed_df.to_excel('sample_files/malformed_data.xlsx', index=False)
    
    # Save CSV versions
    employee_df.to_csv('sample_files/employee_data.csv', index=False)
    sales_df.to_csv('sample_files/sales_data.csv', index=False)
    
    print("Sample files created successfully!")
    print(f"Files generated in the 'sample_files' directory:")
    print("  - employee_data.xlsx - Employee data with inconsistent formats")
    print("  - employee_data.csv  - CSV version of employee data")
    print("  - sales_data.xlsx    - Sales data with currency and date variations")
    print("  - sales_data.csv     - CSV version of sales data")
    print("  - malformed_data.xlsx - Data with intentional issues for cleaning")

if __name__ == "__main__":
    main()