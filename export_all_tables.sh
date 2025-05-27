#!/bin/bash

# Database path
DB_PATH="/home/fetty/electionsproject/elections/elections.accdb"
OUTPUT_DIR="csv_exports"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Get list of tables (one per line)
echo "Getting list of tables..."
mdb-tables -1 "$DB_PATH" | while read -r table; do
    # Skip empty lines and temporary tables (starting with ~)
    if [ -n "$table" ] && [[ ! "$table" =~ ^~ ]]; then
        # Create a safe filename (replace spaces with underscores)
        safe_name=$(echo "$table" | tr ' ' '_')
        output_file="$OUTPUT_DIR/${safe_name}.csv"
        
        echo -n "Exporting '$table' to $output_file... "
        
        # Export the table to CSV
        mdb-export -Q -d ',' -H "$DB_PATH" "$table" > "$output_file" 2>/dev/null
        
        # Check if export was successful
        if [ $? -eq 0 ] && [ -s "$output_file" ]; then
            echo "SUCCESS"
        else
            echo "FAILED"
            # Remove empty output file if it was created
            [ -f "$output_file" ] && rm -f "$output_file"
        fi
    fi
done

echo -e "\nExport complete. Check the '$OUTPUT_DIR' directory for CSV files."
