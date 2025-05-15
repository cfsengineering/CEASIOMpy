
import sys
import subprocess
from pathlib import Path


def main_exec():
    """
    Entry point function for the run_ceasiompy command.

    This function executes the ceasiompy_exec.py script located
    in src/bin within the project root, setting the working directory
    to the project root and passing along all command-line arguments.
    """
    # Define the absolute path to the project root based on the Docker mount.
    PROJECT_ROOT = Path("/CEASIOMpy")

    # Define the path to the ceasiompy_exec.py script relative to the project root.
    SCRIPT_RELATIVE_PATH = Path("src") / "bin" / "ceasiompy_exec.py"
    SCRIPT_ABSOLUTE_PATH = PROJECT_ROOT / SCRIPT_RELATIVE_PATH

    # --- Validation ---

    if not PROJECT_ROOT.is_dir():
        print(f"Error: Project root directory not found at {PROJECT_ROOT}", file=sys.stderr)
        sys.exit(1)

    if not SCRIPT_ABSOLUTE_PATH.is_file():
        print(f"Error: Script not found at {SCRIPT_ABSOLUTE_PATH}", file=sys.stderr)
        sys.exit(1)

    # --- Prepare Command ---

    # Get arguments passed to this entry point (sys.argv[0] is the command name)
    # We pass all arguments from index 1 onwards to the subprocess
    script_args = sys.argv[1:]

    # Construct the command to run
    # Use sys.executable to ensure we use the python interpreter from the current environment
    command = [sys.executable, str(SCRIPT_ABSOLUTE_PATH)] + script_args

    # Optional: Print the command being executed for debugging
    # print(f"Executing command: {' '.join(map(str, command))}", file=sys.stderr)
    # print(f"Working directory: {PROJECT_ROOT}", file=sys.stderr)

    # --- Execute Script ---

    try:
        # Use subprocess.run to execute the command
        # cwd: Set the current working directory for the command to the project root
        # check=True: Raise a CalledProcessError if the script returns a non-zero exit code
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

    except FileNotFoundError:
        msg = (
            "Error: Python interpreter or script not found. "
            f"Command: {' '.join(map(str, command))}"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)  # Indicate failure

    except subprocess.CalledProcessError as e:
        # This happens if the ceasiompy_exec.py script exits with an error code
        print(
            f"Error executing script: The script returned a non-zero exit code {e.returncode}.",
            file=sys.stderr
        )

        if e.stdout:
            print("--- Script stdout ---\n", e.stdout.decode(), file=sys.stderr)

        if e.stderr:
            print("--- Script stderr ---\n", e.stderr.decode(), file=sys.stderr)

        sys.exit(e.returncode)  # Exit the entry point with the script's error code

    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred during script execution: {e}", file=sys.stderr)
        sys.exit(1)  # Indicate failure

    sys.exit(0)  # Indicate success
