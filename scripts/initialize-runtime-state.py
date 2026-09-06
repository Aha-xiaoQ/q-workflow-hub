"""Initialize an explicitly targeted mirror; never infer the user's home."""
import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/q-workflow/scripts"))
from q_base_command import sync_runtime_state

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    state = args.state_root.resolve(strict=True)
    runtime = args.runtime_root.resolve()
    if state == runtime or state in runtime.parents or runtime in state.parents:
        parser.error("Authority and runtime must be separate directories.")
    sync_runtime_state(state, runtime_root=runtime)
