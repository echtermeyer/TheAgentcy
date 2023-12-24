import json

from pathlib import Path
import re

from pydantic import BaseModel, ValidationError
from typing import Any, Tuple, List, Dict


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
        force_code = "Only output this markdown code snippet. Do not output any additional comments."
        return instructions + " " + force_code

    return instructions


def create_model(name: str, fields: List[Tuple[str, Any]]) -> type:
    annotations: Dict[str, Any] = {}
    defaults: Dict[str, Any] = {}
    for field_name, field_type in fields:
        annotations[field_name] = field_type
        defaults[field_name] = ...
    return type(
        name, (BaseModel,), {"__annotations__": annotations, "__default__": defaults}
    )


def extract_json(input_str: str, fields: List[Tuple[str, Any]]) -> dict:
    # Create a dynamic model
    DynamicModel = create_model("DynamicModel", fields)

    # Extract JSON string from the input
    json_str_match = re.search(r"```json\s*(.*?)```", input_str, re.DOTALL)
    if not json_str_match:
        raise ValueError("No JSON string found in the input")

    json_str = json_str_match.group(1).strip()

    # Parse and return the JSON data using the dynamic model
    try:
        parsed_data = DynamicModel.model_validate_json(json_str)
        return parsed_data.model_dump()
    except ValidationError as e:
        raise ValueError(f"Invalid JSON data: {e}")


def parse_response(response: str, parser: dict):
    if parser["use_parser"] == False:
        return response
    if parser["type"] == "code":
        for language in parser["fields"]:
            response = language + ":\n" + extract_code(response, language)
            # print("code parsed")
    elif parser["type"] == "json":
        response = extract_json(response, eval(parser["fields"]))
        # print("JSON parsed")
    else:
        raise ("Invalid type in parser. Use code or json")
    return response  # either the Code string or json


# test_input ="""```json
# {
#         "accepted": true,
#         "text": "The database system to be used is PostgreSQL. The database schema for storing the user's email and name will have a table named 'newsletter_signup' with columns 'id' (integer, primary key), 'email' (string), and 'name' (string). The 'email' field will have a unique constraint to ensure each email is unique. The 'name' field will have a length constraint of maximum 100 characters. There will be authentication and authorization mechanisms using API tokens for accessing the API endpoints. The expected HTTP request methods for the CRUD operations are POST for create, GET for read, PUT for update, and DELETE for delete. Input validation will be required to ensure that the email is in a valid format and that the name is not empty. Error handling will include returning appropriate HTTP status codes for different scenarios such as validation errors or database operation failures."
# }
# ```
# """


# test_fields=[("accepted", bool), ("text", str)]
# test = extract_json(test_input, test_fields)
# print(type(test))
# print(test)
# print("")
# print(test["text"])


# test_respone="This is a respone."
# with open("src/setup/agents.json", "r") as file:
#             config = json.load(file)
# for agent in config:
#     if agent.get("varname") == "database_test":
#          parser = agent["parser"]
# print(parse_response(test_input, 0, parser))
