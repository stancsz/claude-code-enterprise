import json
import os
import sys

def install_governance_plugin():
    settings_dir = os.path.expanduser("~/.claude")
    settings_file = os.path.join(settings_dir, "settings.json")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    plugin_path = os.path.join(repo_root, "plugins", "governance-layer")

    # Simple check: does settings.json exist and contain our plugin path?
    is_installed = False
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                content = f.read()
                if "governance-layer" in content:
                    is_installed = True
        except:
            pass

    if is_installed:
        print("Governance Plugin detected in settings.")
        sys.exit(0)
    else:
        print(f"CRITICAL: Governance Plugin NOT detected in {settings_file}.")
        print("You must install it to proceed with Enterprise Edition.")
        print(f"Run: claude plugin install {plugin_path}")
        sys.exit(1)

if __name__ == "__main__":
    install_governance_plugin()
