import hashlib

def update_version():
    current_version = "1.1.1"  # Change the current_version if needed
    code_hash = hashlib.sha256(open(__file__, "rb").read()).hexdigest()

    try:
        with open("version.txt", "r") as file:
            saved_version, saved_hash = file.read().strip().split(",")
    except FileNotFoundError:
        saved_version, saved_hash = current_version, ""

    if code_hash != saved_hash:
        major, minor, patch = map(int, saved_version.split("."))
        patch += 1
        updated_version = f"{major}.{minor}.{patch}"
        with open("version.txt", "w") as file:
            file.write(f"{updated_version},{code_hash}")
        print(f"Code has changed. New version: {updated_version}")
    else:
        print(f"Code remains unchanged. Version: {saved_version}")

# Call the function when the script is run
if __name__ == "__main__":
    update_version()