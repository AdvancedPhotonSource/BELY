---
alwaysApply: true
---

Always use the .conda/bin Python environment for terminal executions. Prefix Python-related commands with the full path to the conda environment binaries (e.g., '.conda/bin/python' instead of 'python', '.conda/bin/pip' instead of 'pip', '.conda/bin/pytest' instead of 'pytest'). For make commands and other build tools that might invoke Python, ensure the PATH is set to include .conda/bin first or use explicit paths in the commands.