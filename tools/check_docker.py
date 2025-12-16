import subprocess
import shutil

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def check_docker():
    print("Checking Docker Containers...")
    
    if not shutil.which("docker"):
        print(f"{RED}❌ Docker not found in PATH{RESET}")
        return

    try:
        # Run docker ps
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"{RED}❌ Docker Error: {result.stderr.strip()}{RESET}")
            return
            
        containers = result.stdout.strip().split('\n')
        containers = [c for c in containers if c] # Filter empty strings
        
        if containers:
            print(f"{GREEN}✅ Docker is Running! ({len(containers)} active containers){RESET}")
            for c in containers:
                print(f"   - 🐳 {c}")
        else:
            print(f"{RED}⚠️ Docker is running but NO containers are active.{RESET}")
            print("   (Run 'docker-compose up -d' to start VigilAI)")
            
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")

if __name__ == "__main__":
    check_docker()
