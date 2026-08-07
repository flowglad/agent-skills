#!/usr/bin/env python3

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.main import transform


assert transform(" value ") == {"result": "value"}
