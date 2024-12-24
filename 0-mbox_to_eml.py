"""
Mbox to EML Converter

This script converts a mbox file into individual .eml files.
It's designed to work with mbox files and can serve as a reverse operation
for eml_to_mbox.py.

The script:
1. Takes an mbox file as input
2. Extracts each email message
3. Creates individual .eml files in the specified output directory
4. Preserves email headers and content while handling non-ASCII characters

Usage:
    python 0-mbox_to_eml.py input.mbox output_directory

Input:
    A single mbox file
    Example: ./2009.mbox

Output:
    Directory containing individual .eml files
    Example: ./0-originals/2009/
"""

import os
import sys
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from datetime import datetime
from color_utils import *
import re

def decode_header_str(header_str):
    """
    Decode an email header string that might contain encoded parts.
    Returns a decoded unicode string.
    """
    if not header_str:
        return ""
        
    try:
        parts = []
        for b, charset in decode_header(header_str):
            # Handle bytes objects (encoded strings)
            if isinstance(b, bytes):
                try:
                    if charset:
                        parts.append(b.decode(charset))
                    else:
                        parts.append(b.decode('utf-8', 'replace'))
                except (UnicodeDecodeError, LookupError):
                    parts.append(b.decode('utf-8', 'replace'))
            else:
                # Handle string objects
                parts.append(str(b))
        return ''.join(parts)
    except Exception as e:
        print(warning(f"Warning: Could not decode header: {e}"))
        return str(header_str)

def sanitize_filename(subject, date, counter):
    """
    Create a safe filename from the email subject and date.
    Falls back to date only if subject is empty or contains invalid characters.
    """
    if subject:
        # Remove or replace problematic characters
        safe_subject = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in subject)
        safe_subject = safe_subject.strip()[:50]  # Limit length
        if safe_subject:
            return f"{date.strftime('%Y%m%d_%H%M%S')}_{safe_subject}_{counter}.eml"
    
    # Fallback to date only
    return f"{date.strftime('%Y%m%d_%H%M%S')}_{counter}.eml"

def get_email_date(msg):
    """Extract date from email, falling back to current time if not available."""
    try:
        date_str = msg.get('Date')
        if date_str:
            return parsedate_to_datetime(date_str)
    except Exception:
        pass
    return datetime.now()

def split_mbox(mbox_content):
    """
    Split mbox content into individual email messages.
    Returns a list of raw email messages.
    """
    # Regular expression to match mbox message separator
    # This matches "From " at the start of a line, followed by an email address and date
    separator = re.compile(r'(?:^|\n)From [^\n]+\n')
    
    # Split the content at each separator
    messages = separator.split(mbox_content)
    
    # Filter out empty messages and strip whitespace
    return [msg.strip() for msg in messages if msg.strip()]

def save_email_message(message_content, output_path):
    """
    Save an email message to file while preserving encoding.
    """
    try:
        with open(output_path, 'wb') as f:
            # If it's already bytes, write directly
            if isinstance(message_content, bytes):
                f.write(message_content)
            else:
                # Otherwise encode as UTF-8 with replacement for invalid chars
                f.write(message_content.encode('utf-8', errors='replace'))
        return True
    except Exception as e:
        print(error(f"Error saving message: {e}"))
        return False

def convert_to_eml(mbox_path, output_dir):
    """Convert mbox file to individual .eml files."""
    print(header("Mbox to EML Converter"))
    
    # Convert paths to Path objects
    mbox_path = Path(mbox_path)
    output_dir = Path(output_dir)
    
    # Validate input file
    if not mbox_path.exists():
        print(error(f"Error: Mbox file does not exist: {mbox_path}"))
        return False
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read the entire mbox file with UTF-8 encoding and replacement for invalid chars
        print(section("Processing Mbox File"))
        print(info(f"Reading: {mbox_path}"))
        print(info(f"Output directory: {output_dir}"))
        
        with open(mbox_path, 'r', encoding='utf-8', errors='replace') as f:
            mbox_content = f.read()
        
        # Split into individual messages
        messages = split_mbox(mbox_content)
        total_messages = len(messages)
        print(bullet(f"Total messages found: {total_messages}"))
        
        # Track statistics
        processed = 0
        errors = 0
        
        # Process each message
        for i, message_content in enumerate(messages, 1):
            try:
                # Parse the message
                msg = email.message_from_string(message_content)
                
                # Get message date and subject for filename
                date = get_email_date(msg)
                subject = decode_header_str(msg.get('Subject', ''))
                
                # Create unique filename
                filename = sanitize_filename(subject, date, i)
                output_path = output_dir / filename
                
                # Save the message
                if save_email_message(message_content, output_path):
                    processed += 1
                else:
                    errors += 1
                
                # Show progress every 100 files
                if processed % 100 == 0:
                    print(bullet(f"Processed {processed}/{total_messages} emails..."))
                    
            except Exception as e:
                print(error(f"Error processing message {i}: {e}"))
                errors += 1
                continue
        
        # Print final summary
        print(section("Conversion Summary"))
        print(info(f"Input file: {mbox_path}"))
        print(info(f"Output directory: {output_dir}"))
        print(bullet(f"Total messages in mbox: {total_messages}"))
        print(success(f"Successfully converted: {processed} emails"))
        if errors > 0:
            print(error(f"Failed to convert: {errors} emails"))
        
        print(section("Status"))
        if errors == 0:
            print(check("All messages converted successfully"))
        else:
            print(warning(f"Completed with {errors} errors"))
        
        return True
        
    except Exception as e:
        print(error(f"Error processing mbox file: {e}"))
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 0-mbox_to_eml.py input.mbox output_directory")
        print("Example: python 0-mbox_to_eml.py ./2009.mbox ./0-originals/2009")
        sys.exit(1)
    
    if convert_to_eml(sys.argv[1], sys.argv[2]):
        sys.exit(0)
    else:
        sys.exit(1)