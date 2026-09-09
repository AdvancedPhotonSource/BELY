#!/bin/bash

# Copyright (c) UChicago Argonne, LLC. All rights reserved.
# See LICENSE file.

HEADER_CONTENT="--
-- Copyright (c) UChicago Argonne, LLC. All rights reserved.
-- See LICENSE file.
--
"

# Function to add header to a file if it's missing
add_header_if_missing() {
    local file=$1
    if ! grep -q "Copyright (c) UChicago Argonne, LLC. All rights reserved." "$file"; then
        echo "Adding header to $file"
        local temp_file
        temp_file=$(mktemp)
        echo -e "$HEADER_CONTENT" | cat - "$file" > "$temp_file"
        mv "$temp_file" "$file"
    fi
}

# Process all .sql files in the specified directories
for dir in "db/sql/clean" "db/sql/test"; do
    if [ -d "$dir" ]; then
        for file in "$dir"/*.sql; do
            if [ -f "$file" ]; then
                add_header_if_missing "$file"
            fi
        done
    else
        echo "Directory not found: $dir"
    fi
done

echo "Copyright header check complete."
