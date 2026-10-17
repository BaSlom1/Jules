import sys
import os

# Ensure src/ is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import show_settings, show_popup

def main():
    if len(sys.argv) > 1:
        # Mode B: Opened from context menu with a path
        target_path = sys.argv[1]
        show_popup(target_path)
    else:
        # Mode A: Opened directly
        # If it's running as a script or exe, pass sys.executable for registry addition
        # Check if we are running as a compiled exe or a python script
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = f"{sys.executable}\" \"{os.path.abspath(sys.argv[0])}"
        show_settings(exe_path)

if __name__ == "__main__":
    main()
