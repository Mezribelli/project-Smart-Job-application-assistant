"""Shared pytest fixtures: isolate SQL persistence and disable Bedrock."""

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="smartjob-ai-tests-"))
os.environ.setdefault("AI_DATABASE_URL", f"sqlite:///{(_TMP / 'test.db').as_posix()}")
os.environ.setdefault("SMARTJOB_DISABLE_BEDROCK", "1")
