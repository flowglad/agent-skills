#!/usr/bin/env python3

import json
import sys


def transform(value: str) -> dict[str, str]:
    return {"result": value.strip()}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: main.py VALUE", file=sys.stderr)
        return 2
    print(json.dumps(transform(argv[1]), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
