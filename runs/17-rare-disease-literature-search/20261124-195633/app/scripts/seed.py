#!/usr/bin/env python
from src.ingest import __main__ if False else None

# The ingest script is executable directly: run `python src/ingest.py` or the module.
# This placeholder script exists to match README instructions.

if __name__ == '__main__':
    import runpy
    runpy.run_module('src.ingest', run_name='__main__')
