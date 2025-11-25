---
globs: '["**/models.py", "**/*.py"]'
regex: BaseModel
alwaysApply: false
---

Always use Pydantic v2 ConfigDict instead of the deprecated Config class. Use model_config = ConfigDict(...) at the class level. For field aliases, use Field(alias="...") and set populate_by_name=True in ConfigDict to allow both field name and alias during parsing.