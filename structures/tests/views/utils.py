from app_utils.testing import json_response_to_python


def json_response_to_dict(response, key="id") -> dict:
    """Convert JSON response into dict by given key."""
    return {obj[key]: obj for obj in json_response_to_python(response)["data"]}
