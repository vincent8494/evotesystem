#!/bin/bash

# Set up variables
DB_FILE="elections.db"
CSV_DIR="csv_exports"

# Remove existing database if it exists
if [ -f "$DB_FILE" ]; then
    echo "Removing existing database..."
    rm "$DB_FILE"
fi

# Create a new SQLite database and set up the schema
echo "Creating database schema..."
sqlite3 "$DB_FILE" < create_elections_db.sql

# Function to import a CSV file into a table
import_csv() {
    local csv_file="$1"
    local table_name="$2"
    
    if [ ! -f "$csv_file" ]; then
        echo "Warning: $csv_file not found, skipping..."
        return 1
    fi
    
    echo "Importing $csv_file to $table_name..."
    
    # Count lines in the CSV (excluding header)
    local line_count=$(($(wc -l < "$csv_file") - 1))
    
    if [ "$line_count" -eq 0 ]; then
        echo "  No data to import"
        return 0
    fi
    
    # Import the data
    sqlite3 -separator ',' "$DB_FILE" ".mode csv" ".import --skip 1 $csv_file $table_name" 2>/dev/null
    
    # Check if import was successful
    local imported_count=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM $table_name;")
    
    if [ "$imported_count" -gt 0 ]; then
        echo "  Imported $imported_count rows"
        return 0
    else
        echo "  Failed to import data"
        return 1
    fi
}

# Import data from CSV files
echo -e "\nImporting data..."

# Import stream data
import_csv "$CSV_DIR/tbl_stream.csv" "tbl_stream"

# Import teacher data
import_csv "$CSV_DIR/tbl_class_teacher.csv" "tbl_teacher"

# Import class data
import_csv "$CSV_DIR/tbl_class.csv" "tbl_class"

# Import electoral post data
import_csv "$CSV_DIR/tbl_electoral_post.csv" "tbl_electoral_post"

# Import voters data
import_csv "$CSV_DIR/tbl_voters.csv" "tbl_voters"

# Import contestants data
import_csv "$CSV_DIR/tbl_contestants.csv" "tbl_contestants"

# Import results data
import_csv "$CSV_DIR/tbl_results.csv" "tbl_results"

# Import users data
import_csv "$CSV_DIR/tblUser.csv" "tbl_users"

echo -e "\nDatabase setup complete!"
echo "Database file: $DB_FILE"
