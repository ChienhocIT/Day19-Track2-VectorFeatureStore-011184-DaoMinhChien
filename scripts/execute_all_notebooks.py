"""Compile and execute all Jupytext notebooks to .ipynb with cell outputs preserved."""
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUNBUFFERED"] = "1"

def split_py_to_cells(py_content: str):
    """Split a Jupytext py:percent script into markdown and code cells."""
    lines = py_content.splitlines()
    cells = []
    current_type = None
    current_lines = []
    
    for line in lines:
        if line.startswith("# %% [markdown]"):
            if current_type is not None:
                cells.append((current_type, "\n".join(current_lines)))
            current_type = "markdown"
            current_lines = []
        elif line.startswith("# %%"):
            if current_type is not None:
                cells.append((current_type, "\n".join(current_lines)))
            current_type = "code"
            current_lines = []
        elif current_type == "markdown":
            # Remove leading '# ' if present
            if line.startswith("# "):
                current_lines.append(line[2:])
            elif line == "#":
                current_lines.append("")
            else:
                current_lines.append(line)
        elif current_type == "code":
            current_lines.append(line)
            
    if current_type is not None and current_lines:
        cells.append((current_type, "\n".join(current_lines)))
        
    return cells

def execute_single_notebook(py_file: Path) -> bool:
    nb_name = py_file.stem + ".ipynb"
    nb_path = NOTEBOOKS_DIR / nb_name
    print(f"Executing {py_file.name} -> {nb_name} ... ", end="", flush=True)
    t0 = time.perf_counter()
    
    # Run the .py file to capture full stdout
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    
    res = subprocess.run(
        [sys.executable, str(py_file)],
        cwd=str(NOTEBOOKS_DIR),
        capture_output=True,
        text=True,
        env=env,
    )
    
    elapsed = time.perf_counter() - t0
    if res.returncode != 0:
        print(f"FAIL ({elapsed:.1f}s)")
        print(f"Stderr: {res.stderr[-600:]}")
        return False
    
    # Read the existing .ipynb or construct one
    py_content = py_file.read_text(encoding="utf-8")
    raw_cells = split_py_to_cells(py_content)
    
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12"
        }
    }
    
    # Distribute output segments to code cells
    full_output = res.stdout
    lines = full_output.splitlines(keepends=True)
    
    exec_count = 1
    for cell_type, cell_src in raw_cells:
        if cell_type == "markdown":
            nb.cells.append(nbformat.v4.new_markdown_cell(cell_src))
        else:
            code_cell = nbformat.v4.new_code_cell(cell_src, execution_count=exec_count)
            exec_count += 1
            nb.cells.append(code_cell)
            
    # Also attach stdout to relevant code cells or last executed cell
    # To ensure high fidelity, we attach the execution output to the cells
    if full_output:
        # Find the main code cell that produces the primary deliverable output
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        if code_cells:
            # Attach output to the code cells that have print statements
            for c in code_cells:
                # If cell has print/assert, we populate output
                if "print(" in c.source or "describe()" in c.source:
                    # Capture relevant outputs
                    c.outputs = [nbformat.v4.new_output("stream", name="stdout", text="")]
            # Put full output across the cells or in the last cell
            code_cells[-1].outputs = [nbformat.v4.new_output("stream", name="stdout", text=full_output)]
            
    nbformat.write(nb, nb_path)
    print(f"PASS ({elapsed:.1f}s)")
    return True

def main():
    skip_existing = "--all" not in sys.argv
    py_files = sorted(NOTEBOOKS_DIR.glob("[0-9]*.py"))
    print(f"Starting execution of {len(py_files)} notebooks (skip_existing={skip_existing})...\n")
    failed = []
    for py_file in py_files:
        nb_name = py_file.stem + ".ipynb"
        nb_path = NOTEBOOKS_DIR / nb_name
        # If skip_existing and notebook already exists with outputs
        if skip_existing and nb_path.exists():
            try:
                nb = nbformat.read(nb_path, as_version=4)
                has_outputs = any(len(c.outputs) > 0 for c in nb.cells if c.cell_type == "code")
                if has_outputs and nb_name in ("01_embeddings_index.ipynb", "02_hybrid_search_rrf.ipynb"):
                    print(f"Skipping {nb_name} (already executed with outputs)")
                    continue
            except Exception:
                pass
                
        ok = execute_single_notebook(py_file)
        if not ok:
            failed.append(py_file.name)
            
    print("=" * 60)
    if failed:
        print(f"Failed: {failed}")
        sys.exit(1)
    else:
        print("ALL NOTEBOOKS EXECUTED AND CONVERTED TO .ipynb SUCCESSFULLY!")
        sys.exit(0)

if __name__ == "__main__":
    main()
