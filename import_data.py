import sqlite3
import csv
import os
from datetime import datetime

def create_connection(db_file):
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def import_csv_to_table(conn, csv_file, table_name, columns, transform_func=None):
    """Import data from CSV file to SQLite table"""
    try:
        cursor = conn.cursor()
        
        # Read CSV file
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Skip header row
            
            # Prepare placeholders for SQL query
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            # Insert data
            for row in reader:
                if not any(row):  # Skip empty rows
                    continue
                    
                # Transform data if needed
                if transform_func:
                    row = transform_func(row)
                
                # Ensure row has the same number of columns as placeholders
                if len(row) < len(columns):
                    row.extend([None] * (len(columns) - len(row)))
                elif len(row) > len(columns):
                    row = row[:len(columns)]
                
                # Execute insert
                query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                cursor.execute(query, row)
            
            conn.commit()
            print(f"Imported {cursor.rowcount} rows into {table_name}")
            return True
            
    except Exception as e:
        print(f"Error importing {csv_file} to {table_name}: {e}")
        conn.rollback()
        return False

def main():
    # Initialize database
    db_file = 'elections.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # Create database schema
    conn = create_connection(db_file)
    if conn is not None:
        with open('create_elections_db.sql', 'r') as f:
            conn.executescript(f.read())
        print("Created database schema")
    else:
        print("Error: Cannot create database connection")
        return
    
    # Define table import configurations
    import_configs = [
        # (csv_file, table_name, columns, transform_func)
        ('csv_exports/tbl_stream.csv', 'tbl_stream', 
         ['stream_code', 'stream_name', 'stream_id'],
         lambda x: [x[0], f"Stream {x[0].upper()}", x[3]] if len(x) > 3 else x),
        
        ('csv_exports/tbl_class_teacher.csv', 'tbl_teacher',
         ['name', 'gender', 'tsc_number'],
         lambda x: [x[3], x[0], x[4]] if len(x) > 4 else x),
        
        ('csv_exports/tbl_class.csv', 'tbl_class',
         ['class_name', 'stream_id', 'teacher_id'],
         lambda x: [x[0], x[2], None] if len(x) > 2 else x),
        
        ('csv_exports/tbl_electoral_post.csv', 'tbl_electoral_post',
         ['post_name', 'gender_requirement', 'level'],
         lambda x: [x[3], x[1], x[4]] if len(x) > 4 else x),
        
        ('csv_exports/tbl_voters.csv', 'tbl_voters',
         ['gender', 'admission_no', 'full_name', 'class_id', 'stream_id'],
         lambda x: [x[0], x[2], x[3], x[4], x[5]] if len(x) > 5 else x),
        
        ('csv_exports/tbl_contestants.csv', 'tbl_contestants',
         ['contestant_number', 'class_id', 'gender', 'stream_id', 'level', 'full_name', 'post_id'],
         lambda x: [x[0], x[1], x[2], x[3], x[4], x[6], x[9]] if len(x) > 9 else x),
        
        ('csv_exports/tbl_results.csv', 'tbl_results',
         ['valid_votes', 'spoilt_votes', 'result_id', 'class_id', 'level', 'voter_id', 'contestant_name', 'post_id'],
         lambda x: [x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[8]] if len(x) > 8 else x),
        
        ('csv_exports/tbl_users.csv', 'tbl_users',
         ['user_id', 'username', 'role_id', 'password_hash'],
         lambda x: [x[0], x[1], x[2], x[3]] if len(x) > 3 else x)
    ]
    
    # Import data for each table
    for config in import_configs:
        csv_file, table_name, columns, transform_func = config
        if os.path.exists(csv_file):
            print(f"\nImporting {csv_file} to {table_name}...")
            import_csv_to_table(conn, csv_file, table_name, columns, transform_func)
    
    # Close connection
    conn.close()
    print("\nData import completed!")

if __name__ == "__main__":
    main()
