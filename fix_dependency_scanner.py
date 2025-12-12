"""
Script to fix all subprocess.run calls in dependency_scanner.py
"""

import re
from pathlib import Path

def fix_subprocess_calls():
    """Replace all subprocess.run calls with safe_subprocess_run"""
    file_path = Path(__file__).parent / "src" / "quality" / "dependency_scanner.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find subprocess.run calls
    pattern = r'subprocess\.run\((.*?)\)'
    
    # Replacement function
    def replace_subprocess(match):
        args = match.group(1)
        
        # Check if it's already been replaced
        if 'safe_subprocess_run' in args:
            return match.group(0)
        
        # Extract the command list (first argument)
        cmd_match = re.search(r'\[(.*?)\]', args)
        if not cmd_match:
            return match.group(0)
        
        # Add timeout and validate path if cwd is present
        if 'cwd=' in args:
            # Replace cwd=path with cwd=validate_path(path)
            args = re.sub(r'cwd=(\w+)', r'cwd=validate_path(\1)', args)
            
            # Add timeout if not present
            if 'timeout=' not in args:
                args = args.rstrip(',') + ', timeout=30'
        
        # Replace subprocess.run with safe_subprocess_run
        return f'safe_subprocess_run({args})'
    
    # Apply replacements
    content = re.sub(pattern, replace_subprocess, content, flags=re.DOTALL)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed all subprocess.run calls in dependency_scanner.py")

if __name__ == "__main__":
    fix_subprocess_calls()
