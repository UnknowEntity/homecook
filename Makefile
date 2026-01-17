build: 
	uv run python -m nuitka --output-dir=build --follow-imports .\main.py