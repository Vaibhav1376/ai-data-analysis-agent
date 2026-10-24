"""
Backward-compatibility entrypoint for analyst_using_gemini.py.
Fixes spelling typo ('analysist' -> 'analyst').
"""
import runpy
import os

if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "analyst_using_gemini.py")
    runpy.run_path(target, run_name="__main__")
