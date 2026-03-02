---
globs: '["**/pytest.ini", "**/pyproject.toml", "**/test_*.py"]'
alwaysApply: false
---

Always include pytest-asyncio in dev dependencies and configure it properly in pytest.ini with asyncio_mode = auto and asyncio_default_fixture_loop_scope = function. Mark async test functions with @pytest.mark.asyncio decorator.