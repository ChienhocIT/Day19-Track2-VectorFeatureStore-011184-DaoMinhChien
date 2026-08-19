"""Execute all lab notebooks and populate output cells cleanly."""
import ast
import contextlib
import io
import json
import os
import sys
import time
import traceback
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUNBUFFERED"] = "1"

# Ensure repo root and notebooks dir are in sys.path
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(NOTEBOOKS_DIR))

def execute_notebook(nb_path: Path) -> bool:
    print(f"Executing {nb_path.name:<32} ... ", end="", flush=True)
    t0 = time.perf_counter()
    try:
        nb = nbformat.read(nb_path, as_version=4)
        # Create dedicated execution namespace
        namespace = {
            "__name__": "__main__",
            "__file__": str(nb_path),
        }
        # Change cwd to notebooks dir for relative path consistency
        orig_cwd = os.getcwd()
        os.chdir(str(NOTEBOOKS_DIR))
        
        for cell_idx, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            
            source = cell.source
            if not source.strip():
                cell.outputs = []
                cell.execution_count = cell_idx + 1
                continue
            
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            
            # Filter out IPython magic commands if any (e.g. % or !)
            clean_lines = []
            for line in source.splitlines():
                if line.strip().startswith("%") or line.strip().startswith("!"):
                    continue
                clean_lines.append(line)
            clean_source = "\n".join(clean_lines)
            
            outputs = []
            try:
                with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                    # Parse AST to evaluate last expression if applicable
                    parsed = ast.parse(clean_source)
                    if parsed.body and isinstance(parsed.body[-1], ast.Expr):
                        exec_body = ast.Module(body=parsed.body[:-1], type_ignores=[])
                        eval_expr = ast.Expression(body=parsed.body[-1].value)
                        exec(compile(exec_body, filename=str(nb_path), mode="exec"), namespace)
                        last_val = eval(compile(eval_expr, filename=str(nb_path), mode="eval"), namespace)
                        if last_val is not None:
                            # If it's a pandas/polars dataframe or displayable object
                            text_repr = repr(last_val)
                            # If it has _repr_html_
                            data = {"text/plain": text_repr}
                            if hasattr(last_val, "_repr_html_"):
                                data["text/html"] = last_val._repr_html_()
                            outputs.append(nbformat.v4.new_output("execute_result", data=data, execution_count=cell_idx + 1))
                    else:
                        exec(compile(clean_source, filename=str(nb_path), mode="exec"), namespace)
                
                stdout_text = stdout_buf.getvalue()
                if stdout_text:
                    outputs.insert(0, nbformat.v4.new_output("stream", name="stdout", text=stdout_text))
                
                stderr_text = stderr_buf.getvalue()
                if stderr_text:
                    outputs.append(nbformat.v4.new_output("stream", name="stderr", text=stderr_text))
                    
                cell.outputs = outputs
                cell.execution_count = cell_idx + 1
            except Exception as exc:
                stdout_text = stdout_buf.getvalue()
                if stdout_text:
                    outputs.insert(0, nbformat.v4.new_output("stream", name="stdout", text=stdout_text))
                
                tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
                outputs.append(nbformat.v4.new_output("error", ename=type(exc).__name__, evalue=str(exc), traceback=tb_lines))
                cell.outputs = outputs
                cell.execution_count = cell_idx + 1
                nbformat.write(nb, nb_path)
                os.chdir(orig_cwd)
                elapsed = time.perf_counter() - t0
                print(f"FAIL ({elapsed:.1f}s)")
                print(f"  Error in cell {cell_idx}: {exc}")
                return False
                
        nbformat.write(nb, nb_path)
        os.chdir(orig_cwd)
        elapsed = time.perf_counter() - t0
        print(f"PASS ({elapsed:.1f}s)")
        return True
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"FAIL ({elapsed:.1f}s)")
        print(f"  Notebook error: {exc}")
        return False

def main() -> int:
    notebooks = sorted(NOTEBOOKS_DIR.glob("[0-9]*.ipynb"))
    if not notebooks:
        print("No notebooks found to execute.")
        return 1
    
    print(f"Found {len(notebooks)} notebooks to execute:")
    failed = []
    for nb in notebooks:
        success = execute_notebook(nb)
        if not success:
            failed.append(nb.name)
            
    print("=" * 50)
    if failed:
        print(f"FAILED {len(failed)}/{len(notebooks)} notebooks: {', '.join(failed)}")
        return 1
    else:
        print(f"ALL {len(notebooks)}/{len(notebooks)} NOTEBOOKS EXECUTED SUCCESSFULLY!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
