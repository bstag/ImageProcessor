## 2024-05-23 - Zip Slip Prevention in Python
**Vulnerability:** User-controlled filenames were used directly when creating entries in a ZIP file (`zipfile.writestr`). This allows attackers to include path traversal characters (`../`) in the filename, leading to potential file overwrites when the ZIP is extracted (Zip Slip).
**Learning:** `zipfile` module in Python does not automatically sanitize filenames when writing. It faithfully writes whatever path is provided.
**Prevention:** Always sanitize filenames using `os.path.basename()` before using them as entries in a ZIP archive or other file system operations, especially when the filename originates from user input.

## 2024-05-24 - Path Traversal Prevention in os.path.splitext
**Vulnerability:** A Path Traversal vulnerability existed in `get_unique_filename` because `os.path.splitext` preserves directory paths from its input, which were then incorrectly joined with `os.path.join()`. This allows writing files outside of the intended directory when filenames contain `../`.
**Learning:** `os.path.splitext` does not strip directory components. When processing user-supplied filenames for internal storage or file operations, always sanitize the filename first using `os.path.basename` (and replacing slashes where appropriate) to ensure only the base filename is used before splitting or joining.
**Prevention:** Sanitize filenames with `os.path.basename(filename.replace("\\", "/"))` before performing operations like `os.path.splitext` or concatenating paths.

## 2024-05-25 - Insecure Temporary File Prevention (CWE-377)
**Vulnerability:** A vulnerability existed where `tempfile.NamedTemporaryFile(delete=False)` was used. When creating temporary files in shared directories like `/tmp`, this allows for potential symlink attacks and race conditions where attackers can overwrite or interact with files created by a higher privileged process. Additionally, without proper exception handling, `delete=False` can lead to resource exhaustion if files are not explicitly deleted on exit.
**Learning:** `tempfile.NamedTemporaryFile(delete=False)` creates a file in the system temp directory and relies on the developer to explicitly delete it. In some OSes, this file is not secure against symlink attacks from other users. Using `tempfile.TemporaryDirectory()` solves these issues by creating a directory with `0700` permissions (only the owner can read/write/execute) that automatically cleans itself up on exit, making files inside it safe.
**Prevention:** Instead of using `NamedTemporaryFile(delete=False)`, prefer `tempfile.TemporaryDirectory()` to create a secure, restricted temporary workspace directory (`0700` permissions) where input and output files can safely reside.
