# scripts/install_dependencies.py
import subprocess
import sys

def install_dependencies():
    """Install all required dependencies"""
    
    dependencies = [
        'fsspec==2023.12.2',
        's3fs==2023.12.2', 
        'pyarrow==14.0.2',
        'openpyxl==3.1.2',
        'boto3[crt]',
        'pandas[all]'
    ]
    
    print("🔧 Installing missing dependencies...")
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
    
    print("🎉 All dependencies installed!")

if __name__ == "__main__":
    install_dependencies()