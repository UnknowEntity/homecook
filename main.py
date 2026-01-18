import json
from pathlib import Path
import click
import logging
import datetime

from windows_toasts import Toast


from models.course import Course
from models.notification import get_windows_toaster
from models.recipe import Recipe, RecipeMetadata
from models.store import load_recipe_from_store, load_recipe_store


class LogLevel(click.ParamType):
    name = "loglevel"

    def convert(self, value, param, ctx):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in valid_levels:
            self.fail(
                f"{value} is not a valid log level. Choose from {valid_levels}.",
                param,
                ctx,
            )
        return value.upper()


@click.group()
@click.option("--log-path", "-l", type=click.Path(), help="Path to the log file.")
@click.option(
    "--log-level", "-v", default="INFO", help="Logging level.", type=LogLevel()
)
@click.pass_context
def main(
    ctx: click.Context = None,
    log_path: Path | None = None,
    log_level: str = "INFO",
):
    click.echo("Welcome to HomeCook!")
    click.echo("================================")
    click.echo("Starting HomeCook CLI...")

    logger = logging.getLogger("HomeCook_Logger")
    logger.setLevel(getattr(logging, log_level))

    if log_path:
        log_path = Path(log_path)
        log_path.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=log_path.joinpath(
                f"homecook_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
        )

    ctx.obj = {"logger": logger}

    load_recipe_store(logger=logger)


@main.command()
@click.option("--key", "-k", help="Key of the recipe to use")
@click.option("--recipe-file", "-f", type=click.Path(), help="Path to the recipe file.")
@click.option("--config-file", "-c", type=click.Path(), help="Path to the config file.")
@click.pass_context
def single_dish(
    context: click.Context,
    key: str | None = None,
    recipe_file: Path | None = None,
    config_file: Path | None = None,
):
    if not key and not recipe_file:
        raise ValueError("single_dish must have either key or recipe file to run.")

    click.echo("Serving a single dish...")

    toaster = get_windows_toaster()

    logger: logging.Logger = context.obj["logger"]
    logger = logger.getChild("single_dish_logger")

    if key:
        recipe_data = json.loads(load_recipe_from_store(key))
        recipe = Recipe.from_dict(recipe_data, logger=logger, config_path=config_file)
    else:
        logger.info(f"Using recipe file: {recipe_file}")
        recipe = Recipe.from_json(recipe_file, config_path=config_file, logger=logger)

        logger.info(
            f"Recipe '{recipe.metadata.name}' (version {recipe.metadata.version}) loaded."
        )

    toaster.show_toast(Toast(["Begin cooking"]))
    try:
        recipe.cook()
    except Exception as e:
        toaster.show_toast(
            Toast([f"Cooking failed for recipe: {recipe.metadata.name}"])
        )
        raise e

    toaster.show_toast(Toast(["Cooking finished"]))


@main.command()
@click.option(
    "--menu-file",
    "-f",
    type=click.Path(exists=True),
    help="Path to the courses directory.",
)
@click.pass_context
def multi_courses(
    context: click.Context,
    menu_file: Path,
):
    click.echo("Serving multiple courses...")
    toaster = get_windows_toaster()

    logger: logging.Logger = context.obj["logger"]
    logger = logger.getChild("multi_courses_logger")

    logger.info(f"Using menu file: {menu_file}")

    course = Course.from_menu_file(menu_file, logger=logger)

    logger.info(f"Course '{course.title}' loaded with {len(course.recipes)} recipes.")

    course.execute_all_recipes(toaster=toaster)

    logger.info("All recipes finished cooking")
    logger.info("Course completed")

    toaster.show_toast(Toast(["Course complete", "All recipes finished cooking"]))


@main.group()
def utensil():
    click.echo("Using utensil functions...")


@utensil.command()
@click.option(
    "--output-file",
    "-f",
    type=click.Path(),
    default="sample_recipe.json",
    help="Output path for the sample recipe JSON.",
)
@click.option(
    "--store-recipe",
    "-s",
    is_flag=True,
    default=False,
    help="Store the sample recipe in the recipe store.",
)
def create_sample_recipe(output_file: Path, store_recipe: bool):
    sample_recipe = Recipe.create_template_file()
    click.echo("Create sample recipe JSON at: " + str(output_file))

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        import json

        json.dump(sample_recipe, f, indent=4)

    if store_recipe:
        from models.store import add_recipe_to_store

        recipe_key = output_file.stem

        add_recipe_to_store(
            key=recipe_key,
            path=str(output_file),
            description=f"A place holder description for {recipe_key}.",
        )
        click.echo(f"Sample recipe stored in recipe store with key '{recipe_key}'.")


@utensil.command()
@click.option(
    "--output-file",
    "-f",
    type=click.Path(),
    default="sample_course.json",
    help="Output path for the sample course JSON.",
)
def create_sample_course(output_file: Path):
    click.echo("Create sample course JSON at: " + str(output_file))

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    sample_course = Course.to_sample_dict()

    with open(output_file, "w") as f:
        import json

        json.dump(sample_course, f, indent=4)


@utensil.command()
@click.option(
    "--recipe-file",
    "-f",
    type=click.Path(exists=True),
    help="Path to the recipe file to add to the store.",
)
def add_recipe_to_store(recipe_file: Path):
    from models.store import add_recipe_to_store

    if not recipe_file.exists() or not recipe_file.is_file():
        raise FileNotFoundError(f"Recipe file '{recipe_file}' not found.")

    # The recipe inside might be a template recipe and potentially
    # couldn't pass validation check for the entire Recipe class
    # but the metadata for the recipe isn't a object that contain
    # template string
    with open(recipe_file, "r") as f:
        import json

        recipe_data = json.load(f)

        recipe_metadata = RecipeMetadata(**recipe_data.get("metadata", {}))

    key = recipe_metadata.name
    description = recipe_metadata.description

    add_recipe_to_store(
        key=key,
        path=str(recipe_file),
        description=description,
    )

    click.echo("Add a recipe to the recipe store.")


if __name__ == "__main__":
    main()
