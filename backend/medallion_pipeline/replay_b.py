"""Run the supplied B replay with UTF-8 explicitly selected on Windows."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
import merge_recovery
ap=argparse.ArgumentParser();ap.add_argument('--b',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
if not sys.flags.utf8_mode:raise SystemExit('Use python -X utf8 replay_b.py ...')
merge_recovery.BASE=a.b;merge_recovery.run(a.output)
