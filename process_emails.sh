#!/bin/bash

# Initialize error log
echo "Error Log - $(date)" > error.log
echo "===================" >> error.log

# Function to log errors with context
log_error() {
    local step=$1
    local year=$2
    local error_text=$3
    echo -e "\nStep $step - Year $year - $(date)" >> error.log
    echo "-------------------------" >> error.log
    echo "$error_text" >> error.log
}

# Function to capture and log output
process_output() {
    local temp_file=$(mktemp)
    tee -a "$temp_file"
    grep -i "error\|warning\|failed\|skipping" "$temp_file" >> error.log
    rm "$temp_file"
}

echo "Starting email processing script..."

# Step 0: Create originals from mbox
echo "Step 0: Creating original emails from mbox..."
for year in {2006..2024}; do
    echo "Creating original emails for year $year..."
    if ! python 0-mbox_to_eml.py ~/temp/mbox/$year.mbox/mbox ./0-originals/$year/ 2>&1 | process_output; then
        log_error 0 $year "Failed to create original emails from mbox"
    fi
done

# Step 1: Run email date fixer for each year
echo "Step 1: Running email date fixer..."
for year in {2006..2024}; do
    echo "Processing year $year..."
    if ! python 1-email_date_fixer.py "./0-originals/$year/" 2>&1 | process_output; then
        log_error 1 $year "Failed to fix email dates"
    fi
done

# Step 2: Delete duplicates for each year
echo "Step 2: Removing duplicates..."
for year in {2006..2024}; do
    echo "Deduplicating year $year..."
    if ! python 2-delete_duplicates.py "./1-fixed/$year/" 2>&1 | process_output; then
        log_error 2 $year "Failed to remove duplicates"
    fi
done

# Step 3: Convert to mbox format
echo "Step 3: Converting to mbox format..."
if ! python 3-eml_to_mbox.py ./2-deduplicated/ ./3-mbox/all.mbox 2>&1 | process_output; then
    log_error 3 "all" "Failed to convert to mbox format"
fi

# Step 4: Process sent emails
echo "Step 4: Processing sent emails..."

echo "Step 0: Creating original emails from sent mbox..."
if ! python 0-mbox_to_eml.py ~/temp/mbox/sent.mbox/mbox ./0-originals/sent/ 2>&1 | process_output; then
    log_error 0 "sent" "Failed to create original emails from sent mbox"
fi

echo "Step 1: Running email date fixer for sent emails..."
if ! python 1-email_date_fixer.py "./0-originals/sent/" 2>&1 | process_output; then
    log_error 1 "sent" "Failed to fix sent email dates"
fi

echo "Step 2: Removing duplicates in sent..."
if ! python 2-delete_duplicates.py "./1-fixed/sent/" 2>&1 | process_output; then
    log_error 2 "sent" "Failed to remove duplicates in sent emails"
fi

echo "Step 3: Converting to mbox format for sent..."
if ! python 3-eml_to_mbox.py ./2-deduplicated/sent ./3-mbox/sent.mbox 2>&1 | process_output; then
    log_error 3 "sent" "Failed to convert sent emails to mbox format"
fi

# Check if there were any errors
if [ -s error.log ]; then
    echo "Processing complete with errors. Check error.log for details."
    echo -e "\nFinal Status: COMPLETED WITH ERRORS - $(date)" >> error.log
else
    echo "Processing complete successfully!"
    echo -e "\nFinal Status: SUCCESS - $(date)" >> error.log
fi