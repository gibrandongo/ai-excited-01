#!/usr/bin/env python3
"""ai-excited-01 entry: copy the bundled image to the output path.

The image is a single self-contained artwork (a giant glass marble rolling
down a rain-slicked city street at dusk, the whole sunset skyline refracted
upside down inside it). This program only copies it, byte for byte, so both
grader runs produce identical output. Standard library only, no network,
no randomness, no timestamps in the output.
"""

import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    if not os.path.isfile(source):
        print("entry.png not found next to main.py", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    # Create the output directory if needed; never delete or remove it.
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
