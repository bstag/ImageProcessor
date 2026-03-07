## 2024-05-23 - Zip Slip Prevention in Python
**Vulnerability:** User-controlled filenames were used directly when creating entries in a ZIP file (`zipfile.writestr`). This allows attackers to include path traversal characters (`../`) in the filename, leading to potential file overwrites when the ZIP is extracted (Zip Slip).
**Learning:** `zipfile` module in Python does not automatically sanitize filenames when writing. It faithfully writes whatever path is provided.
**Prevention:** Always sanitize filenames using `os.path.basename()` before using them as entries in a ZIP archive or other file system operations, especially when the filename originates from user input.

## 2024-05-24 - Path Traversal Prevention in os.path.splitext
**Vulnerability:** A Path Traversal vulnerability existed in `get_unique_filename` because `os.path.splitext` preserves directory paths from its input, which were then incorrectly joined with `os.path.join()`. This allows writing files outside of the intended directory when filenames contain `../`.
**Learning:** `os.path.splitext` does not strip directory components. When processing user-supplied filenames for internal storage or file operations, always sanitize the filename first using `os.path.basename` (and replacing slashes where appropriate) to ensure only the base filename is used before splitting or joining.
**Prevention:** Sanitize filenames with `os.path.basename(filename.replace("\\", "/"))` before performing operations like `os.path.splitext` or concatenating paths.
