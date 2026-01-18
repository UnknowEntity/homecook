from enum import Enum
from logging import Logger
from string import Template
from models.step.step import Step


class CustomStepAction(Enum):
    EVAL = "EVAL"
    PRINT = "PRINT"


class CustomStep(Step):
    """
    Docstring for CustomStep
    A step that performs a custom script execution.
    """

    action: CustomStepAction
    logger: Logger

    @staticmethod
    def to_sample_dict():
        return (
            super()
            .to_sample_dict()
            .update(
                {
                    "name": "custom_step",
                    "description": "A custom script step (this will execute a custom script in Python)",
                    "parameters": {
                        "script": "params[0] + params[1]",
                        "params": {"0": "Hello, ", "1": "world!"},
                    },
                }
            )
        )

    def execute(self):
        match self.action:
            case CustomStepAction.EVAL:
                return self._eval()
            case CustomStepAction.PRINT:
                return self._print()

    def _print(self):
        message: str = self.parameters.get("message")
        params: dict = self.parameters.get("params")

        if message is None:
            raise ValueError("Missing message for print")

        if params is not None:
            message = Template(message).substitute(params)

        self.logger.info(message)

    def _eval(self):
        step_params: dict[str, any] = self.parameters.get("params", {})

        # This parameters list will get evaluated in the script
        params: list[any] = [param for _, param in step_params.items()]  # noqa: F841

        eval_str: str = self.parameters.get("script", "")

        if eval_str:
            return {"result": eval(eval_str)}

        raise ValueError("No script provided for execution.")
