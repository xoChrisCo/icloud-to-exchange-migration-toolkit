"""
Email Deduplicator

This script removes duplicate emails from a processed email directory by comparing Message-IDs.
It is designed to work with the output from email_date_fixer.py.

Deduplication Strategy:
1. Primary method: Uses Message-ID from email headers (designed to be unique per email)
2. Fallback method: If Message-ID is missing, uses combination of From + To + Date

When selecting which version of a duplicate to keep, the script:
1. Prefers versions with fewer Unicode replacement characters (\ufffd)
2. If tied, selects the file with the shortest path (assuming it's in a more logical location)

Usage:
    python 2-delete_duplicates.py ./1-fixed/2024/

Input:
    Expects a directory of .eml files, typically output from email_date_fixer.py
    Example: ./1-fixed/2024/

Output:
    Creates a new timestamped directory under deduplicated/
    Example: ./2-deduplicated/2024/

Note:
    This script intentionally ignores email body content for deduplication to handle cases
    where the same email might have different encodings of special characters (å,ø,æ, etc.)
"""

import os
import sys
import email
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
from color_utils import *
from datetime import datetime
from folder_utils import setup_output_directory

def get_email_key(file_path):
    """
    Get a unique key for the email based on:
    1. Message-ID (primary)
    2. From + To + Date (fallback)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        msg = email.message_from_string(content)
        
        # Store original content for later comparison
        metadata = {'content': content}
        
        message_id = msg.get('Message-ID', '').strip()
        if message_id:
            # If we have a Message-ID, use it as the key
            key = message_id.lower()
        else:
            # Fallback: combine From + To + Date
            from_addr = msg.get('From', '').lower().strip()
            to_addr = msg.get('To', '').lower().strip()
            date = msg.get('Date', '').strip()
            
            # Create a composite key
            key = f"{from_addr}|{to_addr}|{date}"
        
        return key, metadata
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

def select_best_version(duplicates):
    """
    Select the best version from duplicates by preferring:
    1. Files without Unicode replacement characters (\ufffd)
    2. If tied, take the one with the shortest path (assuming it's in a more logical location)
    """
    return min(duplicates, 
              key=lambda x: (x['metadata']['content'].count('\ufffd'), 
                           len(str(x['path']))))

def process_duplicates(source_path: Path):
    """Process duplicates from source path and create deduplicated output"""
    # Validate source path
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        return
    
    # Create output directory with nested timestamp folders
    output_root = setup_output_directory(source_path, "2-deduplicated")
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Find all duplicates
    duplicates = defaultdict(list)
    total_files = 0
    
    # Process all .eml files
    print(header("Email Deduplicator"))
    print(section("Analyzing Files"))
    for eml_file in source_path.rglob('*.eml'):
        total_files += 1
        key, metadata = get_email_key(eml_file)
        if key:
            duplicates[key].append({
                'path': eml_file,
                'metadata': metadata
            })
    
    # Process each group of emails
    kept_files = 0
    duplicate_groups = 0
    total_duplicates = 0
    
    for key, files in duplicates.items():
        if len(files) > 1:
            duplicate_groups += 1
            total_duplicates += len(files) - 1
            
            # Select the best version
            best_version = select_best_version(files)
            
            # Debug info for duplicates
            print(section(f"Duplicate Group: {key}"))
            print(info(f"Found {len(files)} copies, keeping: {best_version['path'].name}"))
            for f in files:
                if f == best_version:
                    print(check(f"{f['path']}"))
                else:
                    print(bullet(f"{f['path']}"))

            # Copy the best version
            rel_path = best_version['path'].relative_to(source_path)
            new_path = output_root / rel_path
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(best_version['path'], new_path)
            kept_files += 1
        else:
            # Not a duplicate, just copy it
            rel_path = files[0]['path'].relative_to(source_path)
            new_path = output_root / rel_path
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(files[0]['path'], new_path)
            kept_files += 1
    
    # Print summary
    print(section("Deduplication Summary"))
    print(info(f"Source directory: {source_path}"))
    print(info(f"Output directory: {output_root}"))
    print(bullet(f"Total files processed: {total_files}"))
    print(warning(f"Duplicate groups found: {duplicate_groups}"))
    print(error(f"Total duplicates removed: {total_duplicates}"))
    print(success(f"Files kept: {kept_files}"))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python 2-delete_duplicates.py ./1-fixed/2006")
        print("Output will be created in: ./2-deduplicated/2006")
        sys.exit(1)
    
    process_duplicates(Path(sys.argv[1]))