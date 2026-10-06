from json import dump, load
from os.path import join, split
from pydantic import BaseModel
from typing import Any


PYTHON_REGEX = r"^(class\s+\w+.*|def\s+\w+.*):"
MARKDOWN_REGEX = r"^(#{1,6}\s+.*)"
CHUNK_REGEX = r".{{1,{}}}(?=\n|$)|.{{{}}}"


def load_json(path: str) -> Any:
    """Load JSON from a file

    Parameters
    ----------
    path : str
        The path of the file

    Returns
    -------
    Any
        The JSON
    """

    with open(path, "r", encoding="utf-8") as file:
        return load(file)


def dump_json(path: str, model: BaseModel) -> None:
    """Dump a model to a JSON file

    Parameters
    ----------
    path : str
        The path of the file
    model : BaseModel
        The model to dump
    """

    with open(path, "w", encoding="utf-8") as file:
        dump(model.model_dump(), file, indent=2)


def print_json(model: BaseModel) -> None:
    """Print the JSON representation of a model to the console

    Parameters
    ----------
    model : BaseModel
        The model to print
    """

    print(model.model_dump_json(indent=4))


def new_file_path(path: str, folder: str) -> str:
    """Returns the path of the file after changing parent directory

    Parameters
    ----------
    path : str
        The path of the file
    folder : str
        The destination folder

    Returns
    -------
    str
        The final file path
    """

    return join(folder, split(path)[-1])
