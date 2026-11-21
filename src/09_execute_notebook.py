"""Execute the night-browsing notebook in a fresh local kernel and export embedded-output HTML."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, sys, time
EXT = Path(__file__).resolve().parents[1]
for key, folder in [('JUPYTER_RUNTIME_DIR', 'jupyter-runtime'), ('JUPYTER_CONFIG_DIR', 'jupyter-config'),
                    ('IPYTHONDIR', 'ipython'), ('MPLCONFIGDIR', 'matplotlib-cache'), ('XDG_CACHE_HOME', 'cache')]:
    target = EXT / 'logs' / folder; target.mkdir(parents=True, exist_ok=True); os.environ[key] = str(target)
os.environ['JUPYTER_PATH'] = str(EXT / '.jupyter')
os.environ['OPENBLAS_NUM_THREADS'] = '2'; os.environ['OMP_NUM_THREADS'] = '2'
kernel = EXT / '.jupyter/kernels/taobao-night'; kernel.mkdir(parents=True, exist_ok=True)
(kernel / 'kernel.json').write_text(json.dumps({'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                                               'display_name': 'Taobao Night Browsing (Python)', 'language': 'python'}))
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter


def main():
    started = time.time(); path = EXT / 'notebooks/night_browsing_analysis.ipynb'
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=3600, kernel_name='taobao-night', resources={'metadata': {'path': str(EXT)}})
    try:
        client.execute()
    finally:
        nbformat.write(nb, path)
    errors = [o for c in nb.cells if c.cell_type == 'code' for o in c.outputs if o.output_type == 'error']
    assert not errors
    exporter = HTMLExporter(); exporter.exclude_input_prompt = True; exporter.exclude_output_prompt = True
    body, _ = exporter.from_notebook_node(nb); path.with_suffix('.html').write_text(body)
    cells = [c for c in nb.cells if c.cell_type == 'code']
    audit = {'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'fresh_kernel': True,
             'python_executable': sys.executable, 'code_cells': len(cells),
             'executed_code_cells': sum(c.execution_count is not None for c in cells), 'error_outputs': len(errors),
             'elapsed_seconds': time.time() - started, 'html_exported': True}
    (EXT / 'notebooks/execution_audit.json').write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
