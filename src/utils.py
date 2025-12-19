import os
import uuid

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size >= power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def get_unique_filename(original_filename, output_dir, suffix="processed"):
    base, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    new_filename = f"{base}_{suffix}_{unique_id}{ext}"
    return os.path.join(output_dir, new_filename)

def get_file_info(file_path):
    size = os.path.getsize(file_path)
    return {
        "name": os.path.basename(file_path),
        "size_bytes": size,
        "size_formatted": format_bytes(size)
    }

def get_safe_filename_stem(filename):
    """
    Sanitizes the filename to prevent path traversal and returns the filename stem (without extension).
    """
    safe_name = os.path.basename(filename)
    if not safe_name:
        safe_name = "image"

    if '.' in safe_name:
        name_stem = safe_name.rsplit('.', 1)[0]
    else:
        name_stem = safe_name

    return name_stem
