---
globs: "**/*.py"
description: Apply when fixing Python import errors in test files that are in
  subdirectories trying to import from parent directories
alwaysApply: false
---

When Python test files need to import modules from parent directories, use try/except blocks in the module being imported to handle both relative imports (when used as a package) and absolute imports (when imported directly from tests). Example:
```python
try:
    # Try relative imports first (when used as a package)
    from .submodule import Component
except ImportError:
    # Fall back to absolute imports (when imported directly from tests)
    from submodule import Component
```
Also ensure test files add the parent directory to sys.path before importing:
```python
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))
```