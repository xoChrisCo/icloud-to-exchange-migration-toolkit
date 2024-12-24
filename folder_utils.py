"""
Common utilities for folder handling across email migration scripts
"""
from pathlib import Path

def get_unique_folder_name(base_path: Path) -> Path:
    """
    Get a unique folder name by appending (n) if the folder already exists.
    Example: if "2006" exists, returns "2006 (2)"
    """
    if not base_path.exists():
        return base_path
        
    counter = 2
    while True:
        new_path = base_path.parent / f"{base_path.name} ({counter})"
        if not new_path.exists():
            return new_path
        counter += 1

def setup_output_directory(input_path: Path, stage_name: str) -> Path:
    """
    Create output directory based on input folder name.
    Example: for input "./originals/2006", creates "./1-fixed/2006"
    """
    # Get the source folder name (e.g., "2006")
    folder_name = input_path.name
    
    # Create the output path
    output_base = Path.cwd() / stage_name / folder_name
    
    # Get unique name if folder exists
    output_path = get_unique_folder_name(output_base)
    
    # Create the directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    return output_path