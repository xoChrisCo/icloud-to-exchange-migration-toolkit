"""
EML to Mbox Converter

This script converts a directory of .eml files into a single mbox file.
It's designed to work with the output from email_date_fixer.py and delete_duplicates.py
as part of an email migration workflow.

The script:
1. Recursively finds all .eml files in the input directory
2. Extracts the From address and Date from each email
3. Creates proper mbox separator lines ("From sender@example.com Thu Jan 1 00:00:00 2024")
4. Combines all emails into a single mbox file, preserving order by date

Usage:
    python 3-eml_to_mbox.py input_directory output.mbox

Input:
    A directory containing .eml files (can be nested in subdirectories)
    Example: ./2-deduplicated/2024

Output:
    A single mbox file containing all emails
    Example: ./3-mbox/2024.mbox

Note:
    This script assumes the emails have been processed by email_date_fixer.py
    and thus have standardized headers and proper date formatting.
"""

import os
import sys
import email
import email.utils
from datetime import datetime
from color_utils import *
from pathlib import Path
from email.utils import parsedate_to_datetime

def get_default_output_path(input_path: Path) -> Path:
    """Generate default output path for mbox file"""
    folder_name = input_path.name
    return Path.cwd() / "3-mbox" / f"{folder_name}.mbox"

def get_email_date_and_sender(eml_path):
    """
    Extract the date and sender from an email file.
    Returns (datetime_obj, from_address) tuple.
    """
    try:
        with open(eml_path, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f)
            
        # Get and parse the date
        date_str = msg.get('Date')
        if date_str:
            date = parsedate_to_datetime(date_str)
        else:
            # If no date found, use file modification time as fallback
            date = datetime.fromtimestamp(os.path.getmtime(eml_path))
            
        # Get the sender address
        from_header = msg.get('From', '')
        # Extract email address from "Name <email@example.com>" format
        if '<' in from_header and '>' in from_header:
            from_addr = from_header.split('<')[1].split('>')[0]
        else:
            from_addr = from_header.strip()
            
        if not from_addr:
            from_addr = 'unknown@unknown.com'
            
        return date, from_addr
        
    except Exception as e:
        print(f"Error processing {eml_path}: {e}")
        return None, None

def create_mbox_separator(date, from_addr):
    """
    Create an mbox separator line using the email's date and sender.
    Format: From sender@example.com Tue Dec 24 10:12:47 2024
    """
    # Format the date to mbox format (removing timezone info)
    date_str = date.strftime('%a %b %d %H:%M:%S %Y')
    return f"From {from_addr} {date_str}\n"

def convert_to_mbox(input_dir, output_mbox):
    """Convert all .eml files in input_dir to a single mbox file."""
    print(header("EML to Mbox Converter"))
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(error(f"Error: Input directory does not exist: {input_dir}"))
        return False
        
    # Find all .eml files and get their dates for sorting
    print(section("Scanning Directory"))
    email_files = []
    total_found = 0
    
    for eml_path in input_path.rglob('*.eml'):
        total_found += 1
        if total_found % 100 == 0:  # Progress indicator for large directories
            print(info(f"Found {total_found} files..."))
            
        date, from_addr = get_email_date_and_sender(eml_path)
        if date and from_addr:
            email_files.append((date, from_addr, eml_path))
        else:
            print(warning(f"Skipping {eml_path.relative_to(input_path)} - Missing date or sender"))
    
    if not email_files:
        print(error("No valid .eml files found in the input directory"))
        return False
    
    # Sort emails by date
    print(section("Converting Files"))
    print(info(f"Processing {len(email_files)} emails..."))
    
    # Track statistics
    processed = 0
    errors = 0
    
    # Create the mbox file
    with open(output_mbox, 'w', encoding='utf-8') as mbox:
        for date, from_addr, eml_path in email_files:
            try:
                # Write the mbox separator
                separator = create_mbox_separator(date, from_addr)
                mbox.write(separator)
                
                # Copy the email content
                with open(eml_path, 'r', encoding='utf-8') as eml:
                    for line in eml:
                        if line.startswith('From '):
                            line = '>' + line
                        mbox.write(line)
                
                mbox.write('\n')
                processed += 1
                
                # Show progress every 100 files
                if processed % 100 == 0:
                    print(bullet(f"Processed {processed}/{len(email_files)} emails..."))
                
            except Exception as e:
                print(error(f"Error processing {eml_path.relative_to(input_path)}: {e}"))
                errors += 1
                continue
    
    # Print final summary
    print(section("Conversion Summary"))
    print(info(f"Input directory: {input_path}"))
    print(info(f"Output file: {output_mbox}"))
    print(bullet(f"Total files found: {total_found}"))
    print(success(f"Successfully converted: {processed} emails"))
    if errors > 0:
        print(error(f"Failed to convert: {errors} emails"))
    
    print(section("Status"))
    if errors == 0:
        print(check("All files converted successfully"))
    else:
        print(warning(f"Completed with {errors} errors"))
        
    return True

if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print("Usage: python 3-eml_to_mbox.py ./2-deduplicated/2006 [output.mbox]")
        print("If output.mbox is omitted, defaults to ./3-mbox/2006.mbox")
        sys.exit(1)
        
    input_dir = Path(sys.argv[1])
    
    if len(sys.argv) == 3:
        output_mbox = Path(sys.argv[2])
    else:
        output_mbox = get_default_output_path(input_dir)
    
    # Create output directory if it doesn't exist
    output_mbox.parent.mkdir(parents=True, exist_ok=True)
    
    if convert_to_mbox(input_dir, output_mbox):
        sys.exit(0)
    else:
        sys.exit(1)