import json

from typing import Dict
from pathlib import Path
import re

def write_str_to_file(string: str, full_path: Path) -> str:
    with open(full_path, "w") as file:
        file.write(string)

    return full_path


def extract_json_from_str(text: str) -> Dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    extracted = text[start:end]

    if extracted:
        return json.loads(extracted)
    else:
        raise ValueError("No valid JSON found")

def extract_code(input_string, language):
    """
    Extracts a code section from the input string that starts with ```<language>
    and ends with ```.
    
    :param input_string: The string to be parsed.
    :param language: The language specifier (e.g., 'json', 'python').
    :return: Extracted code section or an empty string if not found.
    """
    pattern = f"```{language}(.*?)```"
    match = re.search(pattern, input_string, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return ""
    
def output_format(language: str, code_only: bool) -> str:
    """
    Generates a markdown code snippet with a specified programming language.

    :param language: The language for the code snippet (e.g., 'python', 'javascript').
    :param code_only: A boolean to force that only the code block is outputed.
    :return: A string containing the formatted markdown code snippet.
    """
    instructions = f'The output should be a markdown code snippet, starting with "```{language}" and ending with "```".'
    if code_only:
        force_code = 'Only output this markdown code snippet. Do not output any additional comments.'
        return instructions+' '+force_code

    return instructions