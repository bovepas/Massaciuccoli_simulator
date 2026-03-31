from subprocess import run

VERSION = "versions.v6_1_orchestrator"

if __name__ == "__main__":
    print(f"Launching module {VERSION}\n")
    run(["python", "-m", VERSION])
