from enum import Enum
from pathlib import Path
from pydantic import BaseModel

from models.step.step import Step, StepType
from models.step_status import StepStatus

from playwright.sync_api import Page


class PlayWrightActionType(Enum):
    NAVIGATION = "NAVIGATION"
    CLICK = "CLICK"
    TYPE = "TYPE"
    SELECT = "SELECT"
    CHECK = "CHECK"
    FOCUS = "FOCUS"
    UPLOAD_FILE = "UPLOAD_FILE"
    WAIT_FOR_REQUEST = "WAIT_FOR_REQUEST"
    WAIT_FOR_SELECTOR = "WAIT_FOR_SELECTOR"
    WAIT_AMOUNT_OF_TIME = "WAIT_AMOUNT_OF_TIME"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    TAKE_SCREENSHOT = "TAKE_SCREENSHOT"


class PlayWrightConfig(BaseModel):
    headless: bool = True
    default_timeout: int = 30000  # in milliseconds
    screen_shot_path: Path

    def __post_init__(self):
        self.screen_shot_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        return {
            "headless": True,
            "default_timeout": 30000,
            "screen_shot_path": str(Path("./screenshots").resolve()),
        }


class PlaywrightStep(Step):
    """
    A step that performs actions using Playwright.
    """

    status: StepStatus
    action: PlayWrightActionType
    parameters: dict[str, any]
    page: Page
    screen_shot_path: Path
    default_timeout: int = 30000  # in milliseconds

    @classmethod
    def with_config(cls, config: PlayWrightConfig, **data) -> "PlaywrightStep":
        """Create a PlaywrightStep instance with the provided configuration."""
        return cls(
            **data,
            screen_shot_path=config.screen_shot_path,
            default_timeout=config.default_timeout,
        )

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        """
        Returns a sample dictionary representation of the PlaywrightStep.
        """
        base_dict = super().to_sample_dict()
        base_dict.update(
            {
                "name": "playwright_step",
                "step_type": StepType.PLAYWRIGHT.value,
                "description": "A playwright step (this will open a browser)",
                "action": PlayWrightActionType.NAVIGATION.value,
                "parameters": {"url": "https://example.com"},
            }
        )
        return base_dict

    def execute(self):
        match self.action:
            case PlayWrightActionType.NAVIGATION:
                self._navigate()
            case PlayWrightActionType.CLICK:
                self._click()
            case PlayWrightActionType.TYPE:
                self._type()
            case PlayWrightActionType.SELECT:
                self._select()
            case PlayWrightActionType.CHECK:
                self._check()
            case PlayWrightActionType.FOCUS:
                self._focus()
            case PlayWrightActionType.UPLOAD_FILE:
                self._upload_file()
            case PlayWrightActionType.WAIT_FOR_REQUEST:
                self._wait_for_request()
            case PlayWrightActionType.WAIT_FOR_SELECTOR:
                self._wait_for_selector()
            case PlayWrightActionType.WAIT_AMOUNT_OF_TIME:
                self._wait_amount_of_time()
            case PlayWrightActionType.EXTRACT_TEXT:
                return self._extract_text()
            case PlayWrightActionType.TAKE_SCREENSHOT:
                self.take_screenshot()

    def take_screenshot(self, filename: str = "screenshot.png"):
        filename: str = self.parameters.get("filename", filename)
        screenshot = self.page.screenshot()

        screenshot_path = self.screen_shot_path / filename
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)

    def _navigate(self):
        url: str = self.parameters.get("url")
        if url:
            self.page.goto(url)

    def _click(self):
        selector: str = self.parameters.get("selector")
        if selector:
            self.page.click(selector)

    def _type(self):
        selector: str = self.parameters.get("selector")
        text: str = self.parameters.get("text", "")
        if selector:
            self.page.fill(selector, text)

    def _select(self):
        selector: str = self.parameters.get("selector")
        value: str = self.parameters.get("value", "")
        if selector:
            self.page.select_option(selector, value)

    def _check(self):
        selector: str = self.parameters.get("selector")
        if selector:
            self.page.check(selector)

    def _focus(self):
        selector: str = self.parameters.get("selector")
        if selector:
            self.page.focus(selector)

    def _upload_file(self):
        selector: str = self.parameters.get("selector")
        file_path: str = self.parameters.get("file_path", "")
        timeout: int = self.parameters.get("timeout", self.default_timeout)

        if selector and file_path:
            self.page.set_input_files(selector, file_path, timeout=timeout)

    def _wait_for_request(self):
        url: str = self.parameters.get("url")
        timeout: int = self.parameters.get("timeout", self.default_timeout)
        if url:
            self.page.expect_request(url, timeout=timeout)

    def _wait_for_selector(self):
        selector: str = self.parameters.get("selector")
        timeout: int = self.parameters.get("timeout", self.default_timeout)
        if selector:
            self.page.wait_for_selector(selector, timeout=timeout)

    def _wait_amount_of_time(self):
        amount: int = self.parameters.get("amount", self.default_timeout)
        self.page.wait_for_timeout(amount)

    def _extract_text(self) -> dict[str, str]:
        selector: str = self.parameters.get("selector")
        if selector:
            element = self.page.query_selector(selector)
            if element:
                return {"text": element.inner_text()}

        raise ValueError(
            "Selector not provided or element not found for text extraction."
        )
