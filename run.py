import subprocess
import sys


def run_script(script_name):

    print(f"\n▶ Running {script_name}")

    try:

        result = subprocess.run(
            ["python3", script_name],
            check=True
        )

        print(f"✅ {script_name} completed successfully")

    except subprocess.CalledProcessError:

        print(f"❌ {script_name} failed")
        sys.exit(1)

    except FileNotFoundError:

        print(
            f"❌ python3 not found or "
            f"{script_name} does not exist"
        )
        sys.exit(1)

    except Exception as e:

        print(
            f"❌ Unexpected error while "
            f"running {script_name}: {e}"
        )
        sys.exit(1)


def main():

    # STEP 1
    run_script("run_questions.py")

    # STEP 2
    run_script("evaluate_responses.py")

    print(
        "\n🎉 Pipeline completed successfully"
    )


if __name__ == "__main__":
    main()