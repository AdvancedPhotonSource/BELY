---
alwaysApply: true
---

Always use the .conda/bin Python environment for terminal executions. When running Python-related commands:
1. ALWAYS execute commands from the project root directory to ensure relative conda paths work correctly
2. Use full paths: '.conda/bin/python' instead of 'python', '.conda/bin/pip' instead of 'pip', '.conda/bin/pytest' instead of 'pytest'
3. For make commands and build tools that invoke Python, either:
   - Set PATH explicitly: 'PATH=.conda/bin:$PATH make ...'
   - Or use absolute paths by prefixing with workspace path
4. Never use system Python or assume 'python' is in PATH
5. Always verify you're in the project root before executing commands