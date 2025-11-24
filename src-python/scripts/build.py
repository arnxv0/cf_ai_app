import PyInstaller.__main__
import os
import platform
import shutil

# Get the parent directory (src-python/)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
current_dir = os.path.dirname(os.path.abspath(__file__))

# Determine platform-specific binary name for Tauri sidecar
def get_platform_binary_name():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map to Tauri's expected architecture names
    if machine in ['arm64', 'aarch64']:
        arch = 'aarch64'
    elif machine in ['x86_64', 'amd64']:
        arch = 'x86_64'
    else:
        arch = machine
    
    if system == 'darwin':
        return f'pointer-backend-{arch}-apple-darwin'
    elif system == 'linux':
        return f'pointer-backend-{arch}-unknown-linux-gnu'
    elif system == 'windows':
        return f'pointer-backend-{arch}-pc-windows-msvc.exe'
    else:
        return 'pointer-backend'

platform_binary_name = get_platform_binary_name()

# Change to parent directory to run build
os.chdir(parent_dir)

# Use the custom .spec file for better PyObjC support
PyInstaller.__main__.run([
    'pointer-backend.spec',
    '--clean',
    '--noconfirm',
])

# Rename the binary to platform-specific name
generic_binary = os.path.join('dist', 'pointer-backend')
platform_binary = os.path.join('dist', platform_binary_name)

if os.path.exists(generic_binary):
    shutil.move(generic_binary, platform_binary)
    print(f"✅ Build complete! Binary created at: dist/{platform_binary_name}")
    print("📦 Next step: Copy to Tauri binaries:")
    print(f"   cp dist/{platform_binary_name} ../src-tauri/binaries/")
else:
    print("❌ Build failed: Binary not found")
