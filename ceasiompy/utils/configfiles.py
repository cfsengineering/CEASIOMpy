"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2021-12-10

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from collections import OrderedDict

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


class ConfigFile:
    """Class to read/write and modify a configuration file."""

    def __init__(self, filename=None):
        """Initialize the ConfigFile class.

        Args:
            filename (Path): path to the configuration file.
        """

        self.filename = filename

        self.data = OrderedDict()
        self.comment_idx = 1

        if filename:
            self.read_file(filename)

    def read_file(self, file):
        """Read a .cfg or .txt configuration file."""

        if file.suffix not in [".cfg", ".txt"]:
            raise ValueError("File must be a .cfg or .txt file")

        if not file.is_file():
            raise FileNotFoundError(f"File {file} not found")

        with open(file, "r") as lines:
            for line in lines:
                if not line.strip():
                    continue

                elif line.startswith("%"):
                    key = f"comment_{self.comment_idx}"
                    self.data[key] = line.strip()
                    self.comment_idx += 1

                elif "=" in line:

                    key, value = line.split("=")

                    if ";" in value:
                        value_list = value.split(";")
                        value_list = [v.strip() for v in value_list]

                        self.data[key.strip()] = value_list

                    elif "(" in value and ")" in value:
                        value = value.replace("(", "").replace(")", "")
                        value_list = value.split(",")
                        value_list = [val.strip() for val in value_list]

                        # Check if the list could be a list of floats
                        try:
                            value_list = [float(val) for val in value_list]
                        except ValueError:
                            pass

                        self.data[key.strip()] = value_list

                    elif value.strip().lower() == "none":
                        self.data[key.strip()] = None

                    else:
                        self.data[key.strip()] = value.strip()

                else:
                    raise ValueError(f"Invalid line in file {file}: {line}")

    def write_file(self, file, overwrite=False):
        """Write a .cfg configuration file."""

        if file.is_file():
            if overwrite:
                file.unlink()
            else:
                raise FileExistsError(
                    f"File {file} already exists. Use overwrite=True to overwrite"
                )

        with open(file, "w") as f:
            for key, value in self.data.items():
                if "comment_" in key:
                    if value.startswith("%"):
                        f.write(value + "\n")
                    else:
                        f.write("% " + value + "\n")
                elif value is None:
                    f.write(f"{key} = NONE\n")
                elif isinstance(value, list):
                    if any("(" in str(val) for val in value):
                        f.write(f"{key} = {'; '.join(map(str,value))}\n")
                    else:
                        f.write(f"{key} = ( {', '.join(map(str,value))} )\n")
                else:
                    f.write(f"{key} = {value}\n")

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self) -> str:
        text_line = []
        for key, value in self.data.items():
            if "comment_" in key:
                if value.startswith("%"):
                    text_line.append(value)
                else:
                    text_line.append("% " + value)
            elif value is None:
                text_line.append(f"{key} = NONE\n")
            elif isinstance(value, list):
                if any("(" in str(val) for val in value):
                    text_line.append(f"{key} = {'; '.join(map(str,value))}\n")
                else:
                    text_line.append(f"{key} = ( {', '.join(map(str,value))} )\n")
            else:
                text_line.append(f"{key} = {value}")
        return ("\n").join(text_line)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute")
