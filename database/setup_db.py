
# database/setup_db.py

import sqlite3
import pandas as pd

def create_tables():
    """
    Creates the Crops and Wages tables in the SQLite database.
    """
    conn = sqlite3.connect('farm_management.db')
    cursor = conn.cursor()
    
    # Create Crops table with year column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            yield_amount REAL NOT NULL,
            target REAL NOT NULL
        )
    ''')
    
    # Create Wages table with year column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Wages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            wage REAL NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            time_worked REAL NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Crops and Wages tables created successfully.")

def populate_data():
    """
    Populates the Crops and Wages tables with data from CSV files.
    """
    conn = sqlite3.connect('farm_management.db')
    cursor = conn.cursor()
    
    # Load data from CSV files
    crops_data = pd.read_csv('crops_polish_realistic_agriculture.csv')
    wages_data = pd.read_csv('employee_records_jan2022_dec2024.csv')
    
    # Insert data into Crops table
    for _, row in crops_data.iterrows():
        cursor.execute('''
            INSERT INTO Crops (id, crop_name, month, year, yield_amount, target)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (row['id'], row['crop_name'], row['month'], row['year'], row['yield_amount'], row['target']))
    
    # Insert data into Wages table
    for _, row in wages_data.iterrows():
        cursor.execute('''
            INSERT INTO Wages (id, employee_name, wage, month, year, time_worked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (row['id'], row['employee_name'], row['wage'], row['month'], row['year'], row['time_worked']))
    
    conn.commit()
    conn.close()
    print("Data populated successfully.")

if __name__ == "__main__":
    create_tables()
    populate_data()
