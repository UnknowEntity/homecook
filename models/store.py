import datetime
from logging import Logger
import os
from pathlib import Path
from tomlkit import comment, document, nl, parse, table, TOMLDocument

RECIPES_STORE_FILENAME = "recipes.toml"
RECIPES_STORE_PATH: Path
RECIPES_STORE: TOMLDocument


def add_recipe_to_store(key: str, path: str, description: str) -> None:
    """
    Add a recipe to the recipes store and update the store file.
    """
    global RECIPES_STORE

    if RECIPES_STORE["recipes"].get(key) is not None:
        raise KeyError(f"Recipe with key '{key}' already exists in the recipe store.")

    RECIPES_STORE["recipes"][key] = {
        "path": path,
        "description": description,
        "created_at": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    }

    with open(RECIPES_STORE_PATH, "w") as f:
        f.write(RECIPES_STORE.as_string())


def load_recipe_from_store(key: str) -> str:
    """
    Load a recipe from the recipes store by its key.
    """
    global RECIPES_STORE

    if RECIPES_STORE["recipes"].get(key) is None:
        raise KeyError(f"Recipe with key '{key}' not found in the recipe store.")

    recipe_entry = RECIPES_STORE["recipes"][key]
    recipe_path = Path(recipe_entry["path"])

    with open(recipe_path, "r") as f:
        return f.read()


def load_recipe_store(logger: Logger) -> TOMLDocument:
    """
    Create a TOML file to store recipes if it doesn't exist.
    """

    # Define constants and ensure the recipes store file exists
    global RECIPES_STORE
    global RECIPES_STORE_PATH

    base_store_dir = os.getenv("HOMECOOK_STORE_DIR", str(Path.home()))

    recipes_store = base_store_dir.joinpath(RECIPES_STORE_FILENAME)
    RECIPES_STORE_PATH = recipes_store

    logger.info(f"Using recipe store at: {recipes_store}")

    if not recipes_store.exists():
        with open(recipes_store, "w") as f:
            RECIPES_STORE = create_base_recipe_store()

            f.write(RECIPES_STORE.as_string())
    else:
        with open(recipes_store, "r") as f:
            content = f.read()
            RECIPES_STORE = parse(content)


def create_base_recipe_store() -> TOMLDocument:
    doc = document()
    doc.add(comment(" HomeCook Recipes Store "))
    doc.add(comment(" Add your recipes here in TOML format."))
    doc.add(nl())
    doc.add("title", "My Recipe Store")

    recipes = table()

    recipes.add(
        "sample_recipe",
        {
            "path": "path/to/your/recipe.json",
            "description": "A sample recipe entry",
            "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        },
    )

    doc.add("recipes", recipes)

    return doc
