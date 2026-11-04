"""``pyblender script.py``: run a scene script inside Blender in background mode.

The Blender executable is looked up in ``$BLENDER`` then in ``$PATH``. The directory
holding this pyblender and the current directory are added to Blender's Python path, so
no installation into Blender's bundled Python is needed.
"""

import os
import shutil
import subprocess
import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: pyblender SCRIPT.py [blender options...]")
        return 2

    blender = os.environ.get("BLENDER") or shutil.which("blender")
    if blender is None:
        print("Blender executable not found: set $BLENDER or add blender to $PATH", file=sys.stderr)
        return 1

    # make this very pyblender (and anything in the current directory) importable from Blender
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (os.getcwd(), package_root, env.get("PYTHONPATH")) if p)
    cmd = [blender, "-b", "--python-use-system-env", "--python", argv[0], *argv[1:]]
    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
