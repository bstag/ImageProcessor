with open("src/logging_config.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("<<<<<<< HEAD"):
        skip = True
        new_lines.append("        # Security Enhancement: Use RotatingFileHandler to prevent Disk Exhaustion (DoS)\n")
        new_lines.append("        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)\n")
    elif line.startswith("======="):
        pass
    elif line.startswith(">>>>>>> origin/main"):
        skip = False
    elif not skip:
        new_lines.append(line)

with open("src/logging_config.py", "w") as f:
    f.writelines(new_lines)
