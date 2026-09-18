"""Fact table generators.

Unlike dimensions/ (hundreds to low thousands of rows, one pydantic model
per row), facts run into the millions of rows even at this project's
deliberately small scale (see DR-011), so generation here is vectorised
with numpy/pandas rather than building a pydantic object per row.
"""
