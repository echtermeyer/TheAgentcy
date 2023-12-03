import os


def write_str_to_file(string: str, path: str, file_ending: str) -> str:
    if not os.path.exists(path):
        os.makedirs(path)

    filename = "index" + file_ending
    full_path = os.path.join(path, filename)

    with open(full_path, "w") as file:
        file.write(string)

    return full_path
