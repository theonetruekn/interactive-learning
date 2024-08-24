import os

def tree_py_files(root_dir, prefix=""):
    # Get all files and directories in the current root_dir
    entries = [entry for entry in os.listdir(root_dir) if not entry.startswith('.')]
    
    # Filter Python files
    py_files = [f for f in entries if os.path.isfile(os.path.join(root_dir, f)) and f.endswith('.py')]
    
    # Filter directories that contain Python files
    directories = [d for d in entries if os.path.isdir(os.path.join(root_dir, d))]
    
    # Create a list to hold the output lines
    lines = []
    total_files = len(py_files)
    total_dirs = 0
    
    # Process Python files
    for i, py_file in enumerate(py_files):
        connector = "└── " if i == len(py_files) - 1 and not directories else "├── "
        lines.append(f"{prefix}{connector}{py_file}")
    
    # Process directories
    for i, directory in enumerate(directories):
        sub_prefix = "    " if i == len(directories) - 1 else "│   "
        # Recursively call the function on subdirectories
        sub_tree, sub_files, sub_dirs = tree_py_files(os.path.join(root_dir, directory), prefix + sub_prefix)
        if sub_tree:  # Only include directories that contain Python files
            connector = "└── " if i == len(directories) - 1 else "├── "
            lines.append(f"{prefix}{connector}{directory}/")
            lines.extend(sub_tree)
            total_dirs += 1 + sub_dirs  # Count the current directory plus subdirectories
            total_files += sub_files
    
    return lines, total_files, total_dirs

def generate_tree(root_dir):
    lines, total_files, total_dirs = tree_py_files(root_dir)
    if lines:
        tree_string = f"{root_dir}/\n" + "\n".join(lines)
        summary = f"\n{total_dirs} directories, {total_files} files"
        return tree_string + summary
    return ""
