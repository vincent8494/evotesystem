#!/usr/bin/env python3
import subprocess
import os
import csv
from io import StringIO

def get_tables(db_path):
    """Get list of tables from the database, excluding temporary tables"""
    try:
        result = subprocess.run(
            ['mdb-tables', '-1', db_path],
            capture_output=True, text=True, check=True
        )
        # Filter out temporary tables (those starting with ~)
        tables = [t.strip() for t in result.stdout.split('\n') if t.strip() and not t.startswith('~')]
        return tables
    except subprocess.CalledProcessError as e:
        print(f"Error getting tables: {e}")
        return []

def export_table_to_csv(db_path, table_name, output_dir):
    """Export a single table to CSV"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a safe filename (replace spaces with underscores)
        safe_name = table_name.replace(' ', '_')
        output_file = os.path.join(output_dir, f"{safe_name}.csv")
        
        print(f"Exporting table: {table_name}...")
        
        # Export the table to a temporary file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # Use mdb-export with proper quoting
            cmd = ['mdb-export', '-Q', '-d', ',', '-H', db_path, table_name]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                print(f"  ✗ Error exporting {table_name}: {result.stderr}")
                return False
            
            # Write the output to file
            f.write(result.stdout)
            print(f"  ✓ Successfully exported to {output_file}")
            return True
            
    except Exception as e:
        print(f"  ✗ Error exporting {table_name}: {str(e)}")
        return False

def main():
    db_path = "/home/fetty/electionsproject/elections/elections.accdb"
    output_dir = "csv_exports"
    
    print(f"Starting export from {db_path}")
    
    # Get all tables
    tables = get_tables(db_path)
    
    if not tables:
        print("No tables found in the database.")
        return
    
    print(f"\nFound {len(tables)} tables to export:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    print("\nStarting export process...")
    success_count = 0
    
    for table in tables:
        if export_table_to_csv(db_path, table, output_dir):
            success_count += 1
    
    print(f"\nExport complete. Successfully exported {success_count} out of {len(tables)} tables to '{output_dir}'.")

if __name__ == "__main__":
    main()
