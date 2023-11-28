import os
import uuid

def write_str_to_file(string: str, path: str, file_ending: str) -> str:
    # Ensure the path exists, create it if it doesn't
    if not os.path.exists(path):
        os.makedirs(path)

    # Generate a unique filename
    filename = "gpt_code_backend" + file_ending

    # Construct the full file path
    full_path = os.path.join(path, filename)

    # Write the string to the file
    with open(full_path, 'w') as file:
        file.write(string)

    return full_path
