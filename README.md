# HomeCook

HomeCook is a powerful command-line interface (CLI) tool designed to execute automated "recipes" for tasks involving browser automation, file system operations, and custom Python scripts. It's built with Python and leverages libraries like Playwright for web interactions and Pydantic for data validation.

## Features

- **Modular Recipes**: Define recipes as JSON files with a sequence of steps (jobs).
- **Multiple Step Types**:
  - **Playwright Steps**: Automate browser interactions (navigation, clicking, typing, etc.).
  - **File System Steps**: Perform file operations (create, move, copy, delete files/directories).
  - **Custom Script Steps**: Execute arbitrary Python code via eval (use with caution).
- **Recipe Collections**: Group multiple recipes into "courses" with variable substitution.
- **Flexible Configuration**: Customize timeouts, working directories, and more.
- **Error Handling**: Automatic screenshots on Playwright failures and detailed logging.
- **Sample Generators**: Built-in commands to create sample recipe and course JSON files.

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management (recommended)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/homecook.git
   cd homecook
   ```

2. Install dependencies using uv:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Usage

HomeCook provides a CLI with several commands. Use `--help` for details on options.

### Global Options

- `--log-path` / `-l`: Path to the log file.
- `--log-level` / `-v`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO.

### Commands

#### `single-dish`

Execute a single recipe from a JSON file.

```bash
python main.py single-dish --recipe-file path/to/recipe.json [--config-file path/to/config.json]
```

- `--key` / `-k`: The recipe store key of the recipe to use for this run (required if --recipe-file or -f is omit).
- `--recipe-file` / `-f`: Path to the recipe JSON file (required if --key or -k is omit).
- `--config-file` / `-c`: Path to a separate config JSON file (optional if config is embedded in recipe).

#### `multi-courses`

Execute multiple recipes defined in a course JSON file.

```bash
python main.py multi-courses --menu-file path/to/course.json
```

- `--menu-file` / `-f`: Path to the course JSON file (required).

#### `utensil`

Utility commands for homecook.

##### `create-sample-recipe`

Generate a sample recipe JSON file.

```bash
python main.py utensil create-sample-recipe [--output path/to/output.json] [--store-recipe]
```

- `--output` / `-o`: Output path for the sample recipe. Default: `sample_recipe.json`.
- `--store-recipe` / `-s`: Store the generated sample recipe in the recipe store for easy reference. The recipe is stored with a key derived from the output filename (without extension).

##### `create-sample-course`

Generate a sample course JSON file.

```bash
python main.py utensil create-sample-course [--output path/to/output.json]
```

- `--output` / `-o`: Output path for the sample course. Default: `sample_course.json`.

##### `add-recipe-to-store`

Add an existing recipe file to the recipe store.

```bash
python main.py utensil add-recipe-to-store --recipe-file path/to/recipe.json
```

- `--recipe-file` / `-f`: Path to the recipe JSON file to add (required).

This command extracts the recipe's metadata (name and description) and stores the file path in the recipe store for quick access.

## Recipe Store

HomeCook includes a recipe store for managing and quickly accessing frequently used recipes. The store is loaded on startup and allows recipes to be referenced by keys instead of full paths.

- **Filename**: `recipes.toml`
- **Default Location**: User's home directory (e.g., `C:\Users\username\` on Windows, `/home/username/` on Linux/Mac).
- **Custom Location**: Set the `HOMECOOK_STORE_DIR` environment variable to specify a different directory.
- **Storing Recipes**: Use `utensil add-recipe-to-store` to add a recipe file. It uses the recipe's name as the key and stores the path and description.
- **Accessing Stored Recipes**: Recipes in the store can be used in courses or directly via their keys (future CLI enhancements may support this).
- **Persistence**: The store is persisted in a TOML file for reuse across sessions.

### Example Base Store File

If the store file doesn't exist, a base file is created with the following structure:

```toml
# HomeCook Recipes Store
# Add your recipes here in TOML format.

title = "My Recipe Store"

[recipes]
[recipes.sample_recipe]
path = "path/to/your/recipe.json"
description = "A sample recipe entry"
created_at = "20260117_000000"  # Timestamp when created
```

Each recipe entry includes the file path, description, and creation timestamp.

## Recipe Format

Recipes are defined in JSON format. Here's a sample structure:

```json
{
  "description": "A sample recipe for web scraping and file operations",
  "metadata": {
    "name": "sample_recipe",
    "version": "1.0.0"
  },
  "config": {
    "slow_mode": 1000,
    "cwd": ".",
    "playwright_config": {
      "headless": true,
      "default_timeout": 30000,
      "screen_shot_path": "./screenshots"
    },
    "fs_config": {
      "cwd": "."
    }
  },
  "jobs": [
    {
      "name": "navigate_to_site",
      "job_type": "PLAYWRIGHT",
      "description": "Navigate to a website",
      "action": "NAVIGATION",
      "parameters": {
        "url": "https://example.com"
      }
    },
    {
      "name": "extract_title",
      "job_type": "PLAYWRIGHT",
      "description": "Extract the page title",
      "action": "EXTRACT_TEXT",
      "parameters": {
        "selector": "h1"
      }
    },
    {
      "name": "save_to_file",
      "job_type": "FS",
      "description": "Save extracted text to a file",
      "action": "WRITE_FILE",
      "parameters": {
        "path": "output.txt",
        "content": "${extract_title.text}"
      },
      "parameter_paths": ["content"]
    }
  ]
}
```

### Key Elements

- **metadata**: Name and version of the recipe.
- **config**: Global settings, including Playwright and FS configs.
- **jobs**: Array of steps to execute in order.
  - Each job has a `job_type`, `action`, `parameters`, and optional `parameter_paths` for dynamic values from previous jobs.

#### Parameter Parsing Logic

Steps can produce outputs that are stored throughout the recipe execution. Subsequent steps can reference these outputs using dynamic parameter values.

- **`parameter_paths`**: A list of parameter keys in the step's `parameters` that should be parsed for dynamic values.
- **Dynamic Values**: Instead of static values, use dot-notation paths like `"step_name.output_key"` to reference outputs from previous steps.
- **Example**: If a step named `"extract_title"` outputs `{"text": "Page Title"}`, a later step can set `"parameter_paths": ["content"]` and `"parameters": {"content": "extract_title.text"}` to use the extracted text.

This allows chaining steps where one step's result feeds into another's parameters.

### Step Types

#### Playwright Steps

Actions include NAVIGATION, CLICK, TYPE, SELECT, CHECK, FOCUS, UPLOAD_FILE, WAIT_FOR_REQUEST, WAIT_FOR_SELECTOR, WAIT_AMOUNT_OF_TIME, EXTRACT_TEXT, TAKE_SCREENSHOT.

Example:

```json
{
  "name": "click_button",
  "job_type": "PLAYWRIGHT",
  "action": "CLICK",
  "parameters": {
    "selector": "#submit-button"
  }
}
```

#### File System Steps

Actions: SET_CWD, CREATE_FILE, DELETE_FILE, MOVE_FILE, COPY_FILE, READ_FILE, WRITE_FILE, CREATE_DIRECTORY, DELETE_DIRECTORY, UNZIP_FILE, ZIP_FILE.

Example:

```json
{
  "name": "create_dir",
  "job_type": "FS",
  "action": "CREATE_DIRECTORY",
  "parameters": {
    "path": "new_folder"
  }
}
```

#### Custom Script Steps

Execute Python code using `eval`. Parameters include `script` and `params`.

Example:

```json
{
  "name": "custom_calc",
  "job_type": "CUSTOM_SCRIPT",
  "parameters": {
    "script": "params[0] + params[1]",
    "params": [10, 20]
  }
}
```

**Warning**: Custom scripts use `eval`, which can execute arbitrary code. Use only with trusted recipes.

## Course Format

Courses allow running multiple recipes with shared variables.

```json
{
  "title": "Sample Course",
  "description": "A course with two recipes",
  "recipes": [
    {
      "path": "recipe1.json",
      "variable": {
        "CWD": "/path/to/dir1",
        "HEADLESS": "true"
      }
    },
    {
      "path": "recipe2.json",
      "variable": {
        "CWD": "/path/to/dir2",
        "TIMEOUT": "5000"
      }
    }
  ]
}
```

Variables are substituted into recipe JSON using Python's `string.Template`.

## Configuration

Configs can be embedded in recipes or provided separately. Key settings:

- **slow_mode**: Delay between jobs in milliseconds.
- **cwd**: Working directory.
- **playwright_config**: Browser settings (headless, timeout, screenshot path).
- **fs_config**: File system working directory.

## Examples

1. **Generate Samples**:

   ```bash
   python main.py utensil create-sample-recipe
   python main.py utensil create-sample-course
   ```

2. **Run a Recipe**:

   ```bash
   python main.py single-dish -f sample_recipe.json -v DEBUG
   ```

3. **Run a Course**:

   ```bash
   python main.py multi-courses -f sample_course.json -l logs/homecook.log
   ```

## Development

### Project Structure

- `main.py`: CLI entry point.
- `models/`: Core classes (Recipe, Course, Config, Steps).
- `pyproject.toml`: Project configuration and dependencies.

### Adding New Step Types

1. Extend `StepType` enum in `models/step/step.py`.
2. Create a new step class inheriting from `Step`.
3. Implement `execute()` and `to_sample_dict()`.
4. Update `Recipe.get_job()` to instantiate the new step.

### Testing

Run tests (if any) with your preferred test runner. Ensure Playwright browsers are installed for web steps.

### Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make changes and add tests.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Disclaimer

HomeCook uses `eval` in custom scripts, which can be a security risk. Only run recipes from trusted sources.
