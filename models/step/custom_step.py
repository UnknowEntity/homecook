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

    def to_dict(self):
        return (
            super()
            .to_dict()
            .update(
                {
                    "name": "custom_step",
                    "description": "A custom script step (this will execute a custom script in Python)",
                    "parameters": {
                        "script": self.parameters.get(
                            "script", "params[0] + params[1]"
                        ),
                        "params": self.parameters.get("params", ["Hello, ", "World!"]),
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
        # This parameters list will get evaluated in the script
        params = self.parameters.get("params", [])  # noqa: F841

        eval_str: str = self.parameters.get("script", "")

        if eval_str:
            return {"result": eval(eval_str)}

        raise ValueError("No script provided for execution.")
