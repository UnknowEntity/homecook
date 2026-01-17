from datetime import datetime
import json
from logging import Logger
from pathlib import Path
from pydantic import BaseModel

from models.config import Config
from models.step.custom_step import CustomStep
from models.step.fs_step import FsStep
from models.step.playwright_step import PlaywrightStep
from models.step.step import Step, StepType

from playwright.sync_api import Page


class RecipeMetadata(BaseModel):
    name: str
    version: str
    description: str | None = None


class Recipe(BaseModel):
    metadata: RecipeMetadata
    steps: list[dict[str, any]]
    logger: Logger
    config: Config

    @property
    def use_playwright(self) -> bool:
        for step in self.steps:
            if step.get("step_type") == StepType.PLAYWRIGHT.value:
                return True
        return False

    def __post_init__(self):
        self.logger = self.logger.getChild(self.metadata.name)

    @classmethod
    def from_json(
        cls, path: Path, config_path: Path | None = None, logger: Logger | None = None
    ) -> "Recipe":
        import json

        with open(path, "r") as f:
            recipe = json.load(f)

        if config_path is None and recipe.get("config") is None:
            raise ValueError("No config provided.")

        if config_path:
            with open(config_path, "r") as f:
                config = json.load(f)

            recipe["config"] = config

        return cls.from_dict(recipe, logger=logger)

    @classmethod
    def from_dict(
        cls, data: dict, logger: Logger, config_path: Path | None = None
    ) -> "Recipe":
        if config_path is None and data.get("config") is None:
            raise ValueError("No config provided.")

        if config_path:
            with open(config_path, "r") as f:
                config = json.load(f)

            data["config"] = config

        return cls(
            **data,
            logger=logger if logger else Logger("RecipeLogger"),
        )

    def get_step(self, index: int, page: Page | None = None) -> Step:
        step_data = self.steps[index]
        step_type = StepType(step_data["step_type"])
        match step_type:
            case StepType.PLAYWRIGHT:
                from models.step.playwright_step import PlaywrightStep

                return PlaywrightStep.with_config(
                    self.config.playwright_config, **step_data, page=page
                )

            case StepType.FS:
                from models.step.fs_step import FsStep

                return FsStep.with_config(self.config.fs_config, **step_data)
            case StepType.CUSTOM_SCRIPT:
                from models.step.custom_step import CustomStep

                return CustomStep(**step_data)

    def cook(self) -> None:
        if not self.use_playwright:
            self._cook()
            return

        from playwright.sync_api import sync_playwright

        playwright_config = self.config.playwright_config
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=playwright_config.headless)
            page = browser.new_page()

            self._cook(page=page)

            browser.close()

    def _cook(self, page: Page | None = None) -> None:
        current_step: Step

        params: dict[str, any] = {}

        for step_index in range(len(self.steps)):
            current_step = self.get_step(step_index, page=page)
            self.logger.info(f"Executing step {step_index + 1}/{len(self.steps)}...")
            self.logger.info(
                f"Step type: {current_step.step_type.value} - {current_step.description}"
            )

            try:
                current_step.parse_parameters(params)
                result = current_step.execute()

                if result:
                    params.update({current_step.name: result})

                self.logger.info(f"Step {step_index + 1} completed.")
            except Exception as e:
                if isinstance(current_step, PlaywrightStep):
                    screenshot_path = (
                        self.config.cwd
                        / f"step_{step_index + 1}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    current_step.page.screenshot(path=screenshot_path)
                    self.logger.error(
                        f"Screenshot of the error saved at: {screenshot_path}"
                    )
                self.logger.error(f"Step {step_index + 1} failed with error: {e}")
                raise e

            if self.config.slow_mode > 0:
                import time

                time.sleep(self.config.slow_mode / 1000)

    @staticmethod
    def create_template_file(path: str):
        from pathlib import Path
        import json

        template = {
            "metadata": {
                "name": "sample_recipe",
                "version": "1.0.0",
                "description": "A sample recipe",
            },
            "config": {
                "slow_mode": 0,
                "cwd": ".",
                "playwright_config": PlaywrightStep.PlayWrightConfig.to_sample_dict(),
                "fs_config": FsStep.FsConfig.to_sample_dict(),
            },
            "steps": [
                PlaywrightStep.to_sample_dict(),
                FsStep.to_sample_dict(),
                CustomStep.to_sample_dict(),
            ],
        }

        with open(Path(path), "w") as f:
            json.dump(template, f, indent=4)
