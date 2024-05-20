"""
Implement Python's sitecustomize.py for development purposes.
"""

import coverage

# Ensure coverage is recorded for new processes.
coverage.process_startup()
