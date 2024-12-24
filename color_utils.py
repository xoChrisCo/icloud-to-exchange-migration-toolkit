"""
Console Color Utilities

This module provides consistent color formatting for all email processing scripts.
It uses colorama for cross-platform color support.
"""

from colorama import init, Fore, Style, Back

# Initialize colorama
init()

def success(msg):
    """Print success message in green"""
    return f"{Fore.GREEN}{msg}{Style.RESET_ALL}"

def error(msg):
    """Print error message in red"""
    return f"{Fore.RED}{msg}{Style.RESET_ALL}"

def warning(msg):
    """Print warning message in yellow"""
    return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"

def info(msg):
    """Print info message in cyan"""
    return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"

def highlight(msg):
    """Print highlighted message in magenta"""
    return f"{Fore.MAGENTA}{msg}{Style.RESET_ALL}"

def header(msg):
    """Print header with cyan background"""
    return f"\n{Back.CYAN}{Fore.BLACK} {msg} {Style.RESET_ALL}\n"

def section(name):
    """Print section header with underline"""
    return f"\n{Fore.CYAN}{name}\n{'=' * len(name)}{Style.RESET_ALL}"

def bullet(msg):
    """Print bullet point in cyan"""
    return f"{Fore.CYAN}•{Style.RESET_ALL} {msg}"

def check(msg):
    """Print checkmark in green with message"""
    return f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}"

def cross(msg):
    """Print cross mark in red with message"""
    return f"{Fore.RED}✗{Style.RESET_ALL} {msg}"