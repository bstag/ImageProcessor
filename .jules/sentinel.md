## 2024-05-23 - Zip Slip Prevention in Python
**Vulnerability:** User-controlled filenames were used directly when creating entries in a ZIP file (`zipfile.writestr`). This allows attackers to include path traversal characters (`../`) in the filename, leading to potential file overwrites when the ZIP is extracted (Zip Slip).
**Learning:** `zipfile` module in Python does not automatically sanitize filenames when writing. It faithfully writes whatever path is provided.
**Prevention:** Always sanitize filenames using `os.path.basename()` before using them as entries in a ZIP archive or other file system operations, especially when the filename originates from user input.
