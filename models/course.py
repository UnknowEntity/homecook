import json
import logging
from pathlib import Path
from pydantic import BaseModel
from windows_toasts import Toast, WindowsToaster

from models.recipe import Recipe
from string import Template

from models.store import load_recipe_from_store


class Course(BaseModel):
    title: str
    description: str
    recipes: list[Recipe] = []

    @classmethod
    def from_menu_file(
        cls,
        menu_file: Path,
        logger: logging.Logger,
    ) -> "Course":
        with open(menu_file, "r") as f:
            data = json.load(f)

        recipes_used = data.get("recipes", [])
        recipes: list[Recipe] = []

        if not recipes_used:
            raise ValueError("Course must contain at least one recipe.")

        for recipe_data in recipes_used:
            recipe_variables = recipe_data.get("variable", {})

            recipe_template = Template(load_recipe_text(recipe_data))

            rendered_recipe = recipe_template.substitute(recipe_variables)

            recipe = json.loads(rendered_recipe)

            recipes.append(Recipe.from_dict(recipe, logger=logger))

        return cls(
            title=data.get("title", "Untitled Course"),
            description=data.get("description", ""),
            recipes=recipes,
        )

    def execute_all_recipes(self, toaster: WindowsToaster) -> None:
        for index, recipe in enumerate(self.recipes):
            logging.info(f"Starting recipe: {recipe.metadata.name}")

            toaster.show_toast(
                Toast(["Begin cooking", f"#{index}: {recipe.metadata.name}"])
            )

            try:
                recipe.cook()
            except Exception as e:
                toaster.show_toast(
                    Toast(
                        [
                            "Cooking failed",
                            f"Recipe #{index} ({recipe.metadata.name}) failed to cook",
                        ]
                    )
                )
                raise e

            toaster.show_toast(
                Toast(["Cooking finished", f"Finish {index + 1}/{len(self.recipes)}"])
            )

            logging.info(f"Finished recipe: {recipe.metadata.name}")

    @staticmethod
    def to_sample_dict() -> dict[str, any]:
        return {
            "title": "Sample Course",
            "description": "A sample course containing multiple recipes.",
            "recipes": [
                {
                    "key": "recipe1",
                    "variable": {
                        "CWD": "/path/to/working/directory1",
                        "HEADLESS": "true",
                    },
                },
                {
                    "path": "path/to/recipe2.json",
                    "variable": {
                        "CWD": "/path/to/working/directory2",
                        "SCREEN_SHOT_PATH": "/path/to/screenshot.png",
                        "DEFAULT_TIMEOUT": "5000",
                    },
                },
            ],
        }


def load_recipe_text(data: dict[str, any]) -> str:
    path = data.get("path")
    key = data.get("key")

    if path is None and key is None:
        raise ValueError("Either 'path' or 'key' must be provided to load recipe text.")

    if path:
        recipe_path = Path(path)
        if not recipe_path.exists() or not recipe_path.is_file():
            raise FileNotFoundError(f"Recipe file '{recipe_path}' not found.")

        with open(recipe_path, "r") as f:
            return f.read()

    else:
        return load_recipe_from_store(key)
