import subprocess
import sys


def main():
    filename = sys.argv[1]
    cmd = f"blender -b --python {filename}"
    subprocess.check_output(cmd, shell=True)
