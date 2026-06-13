"""Deploy the DensityGen web app to its HuggingFace Space.

Target: https://huggingface.co/spaces/yushg/densitygen-ald  (Docker SDK, port 7860)

Pushes the runtime files (Dockerfile, pyproject.toml, src/densitygen, web/) and
deliberately leaves the Space's own README.md untouched so its YAML frontmatter
(sdk=docker, app_port=7860) is preserved.

Auth: needs a *write* token. Resolution order:
    1. $HF_WRITE_TOKEN
    2. the CLI-stored login token  (run `huggingface-cli login` with a write token)
    3. $HF_TOKEN  (only used if it happens to have write role)

Run:
    huggingface-cli login        # paste a WRITE token  (once)
    python deploy/hf_space.py
  or:
    HF_WRITE_TOKEN=<your-write-token> python deploy/hf_space.py
"""

from __future__ import annotations

import os
import sys

from huggingface_hub import HfApi, get_token

SPACE_ID = "yushg/densitygen-ald"
ALLOW = ["Dockerfile", "pyproject.toml", "src/densitygen/**", "web/app.py", "web/static/**"]
IGNORE = ["**/__pycache__/**", "**/*.pyc", "**/*.egg-info/**"]


def _write_token() -> str:
    for tok in (os.environ.get("HF_WRITE_TOKEN"), get_token(), os.environ.get("HF_TOKEN")):
        if not tok:
            continue
        try:
            role = HfApi(token=tok).whoami().get("auth", {}).get("accessToken", {}).get("role")
        except Exception:
            continue
        if role == "write":
            return tok
    sys.exit(
        "No write-enabled HuggingFace token found.\n"
        "Run `huggingface-cli login` with a WRITE token, or set HF_WRITE_TOKEN, "
        "then re-run this script."
    )


def main() -> int:
    token = _write_token()
    # Repo root is the parent of deploy/.
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    api = HfApi(token=token)
    commit = api.upload_folder(
        repo_id=SPACE_ID,
        repo_type="space",
        folder_path=root,
        allow_patterns=ALLOW,
        ignore_patterns=IGNORE,
        commit_message="Deploy DensityGen web app + DC viz",
    )
    print("pushed:", getattr(commit, "commit_url", commit))
    print(f"space:  https://huggingface.co/spaces/{SPACE_ID}  (rebuilds automatically)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
