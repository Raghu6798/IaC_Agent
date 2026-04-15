import os
import shutil

# CONFIG
PACKAGE_NAME = "signal_phase_timing"
SRC_DIR = "src"

# folders to move into package
MOVE_DIRS = ["core", "agent", "config", "sandboxes"]

# folders to keep outside (optional)
IGNORE_DIRS = ["assets", "dist", "build", ".git", ".github", "__pycache__"]

def safe_mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created: {path}")

def move_dir(src, dst):
    if not os.path.exists(src):
        print(f"Skipping (not found): {src}")
        return
    
    if os.path.exists(dst):
        print(f"Already exists, skipping: {dst}")
        return
    
    shutil.move(src, dst)
    print(f"Moved: {src} → {dst}")

def create_init_file(path):
    init_file = os.path.join(path, "__init__.py")
    if not os.path.exists(init_file):
        open(init_file, "w").close()
        print(f"Created: {init_file}")

def main():
    print("🚀 Starting restructure...")

    # Step 1: Create src/package
    package_path = os.path.join(SRC_DIR, PACKAGE_NAME)
    safe_mkdir(package_path)

    # Step 2: Move directories
    for folder in MOVE_DIRS:
        src_path = folder
        dst_path = os.path.join(package_path, folder)
        move_dir(src_path, dst_path)

    # Step 3: Ensure __init__.py
    create_init_file(package_path)

    print("✅ Restructure complete!")

if __name__ == "__main__":
    main()