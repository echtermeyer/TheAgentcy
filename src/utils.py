import re

from pathlib import Path
import json

from typing import Any, Tuple, List, Dict
from pydantic import BaseModel, ValidationError


def write_str_to_file(string: str, full_path: Path) -> str:
    with open(full_path, "w") as file:
        file.write(string)

    return full_path


# def extract_code(input_string, language):
#     """
#     Extracts a code section from the input string that starts with ```<language>
#     and ends with ```.

#     :param input_string: The string to be parsed.
#     :param language: The language specifier (e.g., 'json', 'python').
#     :return: Extracted code section or an empty string if not found.
#     """
#     pattern = f"```{language}(.*?)```"
#     match = re.search(pattern, input_string, re.DOTALL)

#     if match:
#         return match.group(1).strip()
#     else:
#         return ""


# def create_model(name: str, fields: List[Tuple[str, Any]]) -> type:
#     annotations: Dict[str, Any] = {}
#     defaults: Dict[str, Any] = {}
#     for field_name, field_type in fields:
#         annotations[field_name] = field_type
#         defaults[field_name] = ...

#     return type(
#         name, (BaseModel,), {"__annotations__": annotations, "__default__": defaults}
#     )


# def extract_json(input_str: str, fields: List[Tuple[str, Any]]) -> dict:
#     # Create a dynamic model
#     # print(f"INPUT_STR: {input_str}")
#     DynamicModel = create_model("DynamicModel", fields)

#     # Extract JSON string from the input
#     json_str_match = re.search(r"```json\s*(.*?)```", input_str, re.DOTALL)
#     if not json_str_match:
#         raise ValueError("No JSON string found in the input")

#     json_str = json_str_match.group(1).strip()

#     # Parse and return the JSON data using the dynamic model
#     try:
#         parsed_data = DynamicModel.model_validate_json(json_str)
#         return parsed_data.model_dump()
#     except ValidationError as e:
#         raise ValueError(f"Invalid JSON data: {e}")


# def parse_response(response: str, parser: dict):
#     if parser["use_parser"] == False:
#         return response
#     if parser["type"] == "code":
#         for language in parser["fields"]:
#             response = extract_code(response, language)
#     elif parser["type"] == "json":
#         response = extract_json(response, eval(parser["fields"]))
#     else:
#         raise ("Invalid type in parser. Use code or json")
#     return response  # either the Code string or json



def parse_message(message:str, parser:dict):
    if parser["use_parser"] == False:
        return message
    
    if parser["type"] == "code":
        language = parser["fields"][0]
        pattern = f"```{language}(.*?)```"

    elif parser["type"] == "json":
        pattern = r"```json\s*(.*?)```"
    
    regex_obj = re.search(pattern, message, re.DOTALL)
    string_dict = regex_obj.group(1).strip()
    
    result = string_dict
    
    if parser["type"] == "json":
        result = json.loads(string_dict)

    return result  

