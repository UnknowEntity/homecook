from enum import Enum
from pathlib import Path

from pydantic import BaseModel

from models.step.step import Step, StepType
from models.step_status import StepStatus


class FsStepAction(Enum):
    SET_CWD = "SET_CWD"
    CREATE_FILE = "CREATE_FILE"
    DELETE_FILE = "DELETE_FILE"
    MOVE_FILE = "MOVE_FILE"
    COPY_FILE = "COPY_FILE"
    READ_FILE = "READ_FILE"
    WRITE_FILE = "WRITE_FILE"
    CREATE_DIRECTORY = "CREATE_DIRECTORY"
    DELETE_DIRECTORY = "DELETE_DIRECTORY"
    UNZIP_FILE = "UNZIP_FILE"
    ZIP_FILE = "ZIP_FILE"


class FsConfig(BaseModel):
    cwd: Path

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        return {"cwd": str(Path(".").resolve())}


class FsStep(Step):
    """
    A step that performs filesystem operations.
    """

    status: StepStatus
    action: FsStepAction
    parameters: dict[str, any]
    cwd: Path

    @classmethod
    def with_config(cls, config: FsConfig, **data) -> "FsStep":
        return cls(**data, cwd=config.cwd)

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        return (
            super()
            .to_sample_dict()
            .update(
                {
                    "name": "fs_step",
                    "step_type": StepType.FS,
                    "description": "A filesystem step (this will perform file system operations)",
                    "action": FsStepAction.SET_CWD.value,
                }
            )
        )

    def execute(self):
        match self.action:
            case FsStepAction.SET_CWD:
                new_cwd: Path = Path(self.parameters["new_cwd"])
                self.cwd = new_cwd
            case FsStepAction.CREATE_FILE:
                return self._create_file()
            case FsStepAction.DELETE_FILE:
                return self._delete_file()
            case FsStepAction.MOVE_FILE:
                return self._move_file()
            case FsStepAction.COPY_FILE:
                return self._copy_file()
            case FsStepAction.READ_FILE:
                return self._read_file()
            case FsStepAction.WRITE_FILE:
                return self._write_file()
            case FsStepAction.CREATE_DIRECTORY:
                return self._create_directory()
            case FsStepAction.DELETE_DIRECTORY:
                return self._delete_directory()
            case FsStepAction.UNZIP_FILE:
                return self._unzip_file()
            case FsStepAction.ZIP_FILE:
                return self._zip_file()

    def _create_file(self):
        value: str = self.parameters.get("value", "")
        file_path: Path = self.cwd / self.parameters["file_path"]

        with open(file_path, "w") as f:
            f.write(value)

        return {"file_path": str(file_path)}

    def _delete_file(self):
        file_path: Path = self.cwd / self.parameters["file_path"]

        if file_path.exists() and file_path.is_file():
            file_path.unlink()

    def _move_file(self):
        source_path: Path = self.cwd / self.parameters["source_path"]
        destination_path: Path = self.cwd / self.parameters["destination_path"]

        if source_path.exists() and source_path.is_file():
            source_path.rename(destination_path)

            return {"destination_path": str(destination_path)}

        raise FileNotFoundError(f"Source file '{source_path}' does not exist.")

    def _copy_file(self):
        import shutil

        source_path: Path = self.cwd / self.parameters["source_path"]
        destination_path: Path = self.cwd / self.parameters["destination_path"]

        if source_path.exists() and source_path.is_file():
            shutil.copy2(source_path, destination_path)

            return {"destination_path": str(destination_path)}

        raise FileNotFoundError(f"Source file '{source_path}' does not exist.")

    def _read_file(self):
        file_path: Path = self.cwd / self.parameters["file_path"]

        if file_path.exists() and file_path.is_file():
            with open(file_path, "r") as f:
                content = f.read()
            return {"content": content}

        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    def _write_file(self):
        value: str = self.parameters.get("value", "")
        file_path: Path = self.cwd / self.parameters["file_path"]

        with open(file_path, "w") as f:
            f.write(value)

        return {"file_path": str(file_path)}

    def _create_directory(self):
        dir_path: Path = self.cwd / self.parameters["dir_path"]
        dir_path.mkdir(parents=True, exist_ok=True)

        return {"dir_path": str(dir_path)}

    def _delete_directory(self):
        import shutil

        dir_path: Path = self.cwd / self.parameters["dir_path"]
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)

    def _unzip_file(self):
        import zipfile

        zip_path: Path = self.cwd / self.parameters["zip_path"]
        extract_to: Path = self.cwd / self.parameters["extract_to"]

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        return {"extracted_to": str(extract_to)}

    def _zip_file(self):
        import zipfile

        file_paths: list[Path] = [
            self.cwd / Path(p) for p in self.parameters["file_paths"]
        ]
        zip_path: Path = self.cwd / self.parameters["zip_path"]

        with zipfile.ZipFile(zip_path, "w") as zip_ref:
            for file_path in file_paths:
                zip_ref.write(file_path, arcname=file_path.name)

        return {"zip_path": str(zip_path)}
