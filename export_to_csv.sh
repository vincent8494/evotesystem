#!/bin/bash

# Database path
DB_PATH="/home/fetty/electionsproject/elections/elections.accdb"
OUTPUT_DIR="csv_exports"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Get list of tables (excluding temporary tables that start with ~)
tables=$(mdb-tables -1 "$DB_PATH" | grep -v '^~')

# Export each table to CSV
echo "Exporting tables to CSV..."
for table in $tables; do
    # Replace spaces with underscores in table name for filename
    safe_table_name=$(echo "$table" | tr ' ' '_')
    output_file="$OUTPUT_DIR/${safe_table_name}.csv"
    
    echo "Exporting $table to $output_file"
    
    # Export the table to CSV
    mdb-export -Q -d ',' -H "$DB_PATH" "$table" > "$output_file"
    
    # Check if export was successful
    if [ $? -eq 0 ]; then
        echo "  ✓ Success"
    else
        echo "  ✗ Failed to export $table"
    fi
done

echo -e "\nExport complete. CSV files are in the '$OUTPUT_DIR' directory."
