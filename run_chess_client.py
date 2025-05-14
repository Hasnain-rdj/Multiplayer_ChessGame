# Launcher script to run the chess client as a module for PyInstaller packaging
import runpy
import sys
import os

if __name__ == "__main__":
    # Detect if running in a PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller: folders are unpacked to _MEIPASS
        bundle_dir = sys._MEIPASS
        sys.path.insert(0, os.path.join(bundle_dir, 'client'))
        sys.path.insert(0, os.path.join(bundle_dir, 'common'))
        sys.path.insert(0, bundle_dir)
        os.chdir(bundle_dir)
    else:
        # Normal script: use project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = script_dir
        os.chdir(project_root)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    runpy.run_module("client.client_main", run_name="__main__")
