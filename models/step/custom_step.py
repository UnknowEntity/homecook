from models.step.step import Step


class CustomStep(Step):
    """
    Docstring for CustomStep
    A step that performs a custom script execution.
    """

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
        # This parameters list will get evaluated in the script
        params = self.parameters.get("params", [])  # noqa: F841

        eval_str: str = self.parameters.get("script", "")

        if eval_str:
            return {"result": eval(eval_str)}

        raise ValueError("No script provided for execution.")
