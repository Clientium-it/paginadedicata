"""rebuild_local.py REQUEST.json WORKDIR: run_batch without the VPS steps; WORKDIR must already hold vq_out.json (+ logos.json, logos/). Used for re-verified rows."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import run_batch
_sh=run_batch.sh
run_batch.sh=lambda c: None if c.lstrip().startswith(('ssh','scp')) else _sh(c)
run_batch.main()
