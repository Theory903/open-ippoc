
import os
import sys
import subprocess
import time
import shutil
import venv
from pathlib import Path

# Configuration
WORKSPACE_ROOT = Path(os.getcwd())
DIST_DIR = WORKSPACE_ROOT / "dist"
TEST_ENV_DIR = Path("/tmp/ippoc-release-test")
PYTHON_EXE = TEST_ENV_DIR / "bin" / "python"
IPPOC_EXE = TEST_ENV_DIR / "bin" / "ippoc"

def print_step(msg):
    print(f"\n🔹 {msg}")

def run_cmd(cmd, cwd=None, env=None, capture=False, check=True):
    if env is None:
        env = os.environ.copy()
    
    # Critical: Unset PYTHONPATH to avoid picking up local source
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    
    print(f"   $ {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        env=env, 
        check=check, 
        text=True, 
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None
    )
    if capture:
        return result.stdout.strip()
    return result

def main():
    print("🚀 Starting IPPOC Release Candidate A-Z Verification (Iso-Mode)")

    # 1. Clean previous test environment
    if TEST_ENV_DIR.exists():
        print_step("Cleaning previous test environment...")
        shutil.rmtree(TEST_ENV_DIR)

    # 2. Create Virtual Environment
    print_step("Creating virtual environment...")
    venv.create(TEST_ENV_DIR, with_pip=True)

    # 3. Install Wheel
    print_step("Installing Release Candidate Wheel...")
    wheels = sorted(list(DIST_DIR.glob("*.whl")), key=lambda p: p.stat().st_mtime, reverse=True)
    if not wheels:
        print("❌ No wheels found in dist/")
        sys.exit(1)
    
    wheel_path = wheels[0]
    print(f"   Found wheel: {wheel_path}")
    
    # Install
    run_cmd([str(PYTHON_EXE), "-m", "pip", "install", "--force-reinstall", str(wheel_path)])

    # 3b. Debug: Inspect installed package structure
    print_step("Inspecting installed package structure...")
    site_packages = run_cmd([str(PYTHON_EXE), "-c", "import site; print(site.getsitepackages()[0])"], capture=True).strip()
    print(f"   Site Packages: {site_packages}")
    run_cmd(["ls", "-R", f"{site_packages}/ippoc"], check=False)

    # 4. Verify Installation
    print_step("Verifying installation...")
    # Run from /tmp to ensure we don't pick up local files
    version_out = run_cmd([str(PYTHON_EXE), "-m", "pip", "show", "ippoc-platform"], capture=True, cwd="/tmp")
    print(version_out)
    
    if "0.9.0" not in version_out:
        print("❌ Incorrect version installed!")
        sys.exit(1)
        
    if "src" in version_out and "Location:" in version_out:
        # Check if Location points to source
        for line in version_out.splitlines():
            if line.startswith("Location:") and "/src" in line and "site-packages" not in line:
                 print("❌ Installation is leaking source directory! Aborting.")
                 sys.exit(1)

    # 5. Start IPPOC Services (Background)
    print_step("Starting IPPOC Services (ippoc run)...")
    
    # Use clean env for process
    proc_env = os.environ.copy()
    proc_env["IPPOC_BASE_DIR"] = "/tmp/ippoc_home"
    proc_env["PYTHONUNBUFFERED"] = "1"
    proc_env["IPPOC_API_KEY"] = "verifyme123" # Fixed key for verification
    if "PYTHONPATH" in proc_env: del proc_env["PYTHONPATH"]

    log_file = open("/tmp/ippoc_service.log", "w")
    ippoc_process = subprocess.Popen(
        [str(IPPOC_EXE), "run", "test_instance", "--db", "sqlite"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=proc_env,
        cwd="/tmp" # Important: Run outside source tree
    )
    
    print("   Services started with PID:", ippoc_process.pid)

    try:
        # 6. Poll for Health
        print_step("Waiting for system health...")
        max_retries = 30
        healthy = False
        
        for i in range(max_retries):
            try:
                # We use the CLI to check status
                result = subprocess.run(
                   [str(IPPOC_EXE), "status"],
                   capture_output=True,
                   text=True,
                   env=proc_env,
                   cwd="/tmp"
                )
                
                if "operational" in result.stdout.lower() or "active" in result.stdout.lower() or "healthy" in result.stdout.lower():
                    print(f"   ✅ System is healthy! (Attempt {i+1})")
                    print(result.stdout)
                    healthy = True
                    break
            except Exception as e:
                pass
            
            if ippoc_process.poll() is not None:
                print("❌ Process exited prematurely!")
                break

            time.sleep(1)
            print(f"   ...waiting ({i+1}/{max_retries})")

        # Cleanup
        if os.path.exists("/tmp/ippoc_service.log"):
            print_step("Service Log Output:")
            with open("/tmp/ippoc_service.log", "r") as f:
                  print(f.read())


        # 7. Functional Test: Ingest Signal
        print_step("Testing Signal Ingestion...")
        run_cmd([str(IPPOC_EXE), "signal", "ingest", "SIGHT", "Release verification test object"], env=proc_env, cwd="/tmp")

        # 8. Functional Test: List Intents
        print_step("Testing Intent Listing...")
        intents_out = run_cmd([str(IPPOC_EXE), "intents"], capture=True, env=proc_env, cwd="/tmp")
        print(intents_out)
        
        print("\n✅ A-Z VERIFICATION PASSED SUCCESSFULLY")

    finally:
        print_step("Tearing down...")
        ippoc_process.terminate()
        try:
            ippoc_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ippoc_process.kill()
        
        # Cleanup
        # shutil.rmtree("/tmp/ippoc_home", ignore_errors=True)

if __name__ == "__main__":
    main()
