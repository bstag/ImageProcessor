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
    Return a sanitized filename stem (name without directory or extension).

    The input is first cleaned of null bytes and then reduced to its basename
    by replacing backslashes with forward slashes and then using
    ``os.path.basename`` to avoid path traversal. If this basename is empty
    (for example, when ``filename`` is an empty string), or consists only of
    dots, a fallback name of ``"image"`` is used.

    The extension is then stripped by splitting on the last dot. Note that
    if the basename starts with a dot and contains no other dots (for example,
    ``".hidden"``), the resulting stem will be an empty string. A fallback
    name of ``"image"`` is used in this case as well.
    """
    # Remove null bytes
    filename = filename.replace('\0', '')

    # Replace backslashes with forward slashes for cross-platform compatibility
    safe_name = os.path.basename(filename.replace("\\", "/"))

    # Handle cases like "" or ".." or "."
    if not safe_name or safe_name.strip('.') == '':
        safe_name = "image"

    if '.' in safe_name:
        name_stem = safe_name.rsplit('.', 1)[0]
    else:
        name_stem = safe_name

    if not name_stem or name_stem.strip('.') == '':
        name_stem = "image"
    return name_stem

def validate_upload_constraints(files, max_count=50, max_total_size_mb=200):
    """
    Validates that the uploaded files do not exceed the file count or total size limits.

    Args:
        files (list): List of file-like objects (must have .size attribute in bytes).
        max_count (int): Maximum allowed number of files.
        max_total_size_mb (int): Maximum allowed total size in Megabytes.

    Returns:
        tuple: (bool, str or None) - (True, None) if valid, (False, error_message) if invalid.
    """
    if len(files) > max_count:
        return False, f"Too many files. Maximum allowed is {max_count}."

    total_size = sum(f.size for f in files)
    total_size_mb = total_size / (1024 * 1024)
    if total_size_mb > max_total_size_mb:
        return False, f"Total upload size ({total_size_mb:.1f} MB) exceeds limit of {max_total_size_mb} MB."

    return True, None
