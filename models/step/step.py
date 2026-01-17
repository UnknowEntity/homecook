from enum import Enum
from pydantic import BaseModel


class StepType(Enum):
    PLAYWRIGHT = "PLAYWRIGHT"
    FS = "FS"
    CUSTOM_SCRIPT = "CUSTOM_SCRIPT"


class Step(BaseModel):
    """
    Base class for all Steps.
    """

    name: str
    step_type: StepType
    description: str
    parameters: dict[str, any]
    parameter_paths: list[str] | None = None

    def execute(self) -> None | any:
        raise NotImplementedError("Execute method must be implemented in subclasses")

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        return {
            "name": "step_name",
            "step_type": StepType.CUSTOM_SCRIPT.value,
            "description": "A custom script step",
            "parameters": {},
            "parameter_paths": None,
        }

    def parse_parameters(self, total_steps_params: dict[str, any]):
        """
        This function is use for parsing parameter for each step.

        A step could have an output and the output will be keep for the entire
        recipe run. The next step could use the output from the previous step for
        it value.

        Ex: An FS Step create file output is the file path and could be use in
        a upload file step

        The parameter_paths of a step will point to the parameter that need parsing,
        while the value of the parsing parameter will be the path to the output to use.

        Ex:  parameter_paths: ["selector"]\n
        This will look for the selector field in parameters.
        If the selector field have the value of "extract_text_from_header.text",
        then the value will be extract from the output "text" of task "extract_text_from_header"

        :param self:
        :param total_steps_params: The entire output for all the step for the recipe.
        :type total_steps_params: dict[str, any]
        """
        if not self.parameter_paths:
            return

        for path in self.parameter_paths:
            keys = path.split(".")

            value = self.parameters

            last_key = keys.pop()

            value = get_value_from_path(value, keys)

            parse_value = get_value_from_path(
                total_steps_params, value[last_key].split(".")
            )

            value[last_key] = parse_value


def get_value_from_path(data: dict[str, any], keys: list[str]) -> any:
    # Empty keys return whole object
    if not keys:
        return data

    value = data
    full_path = ".".join(keys)

    for key in keys:
        if key not in value:
            raise KeyError(f"Key '{key}' not found while accessing path '{full_path}'")
        value = value[key]

    return value
