from pydantic import BaseModel
from models.step.playwright_step import PlayWrightConfig
from models.step.fs_step import FsConfig


class Config(BaseModel):
    slow_mode: int = 0  # in milliseconds
    cwd: str = "."
    playwright_config: PlayWrightConfig | None = None
    fs_config: FsConfig | None = None
