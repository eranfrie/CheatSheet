# CheatSheet

A productivity tool to manage and search snippets.

**NOTE:** This project is forked from [Bookmarker](https://github.com/eranfrie/Bookmarker)
and was quickly modified to make it work.
Therefore it contains inaccuracies (variable namings, comments) and broken tests.


## Installation

##### Requirements:

1. Python 3.7 or higher

##### Linux / macOS:

1. Create a directory named `venv`
2. Run:
```
python -m venv <route/to/venv-directory>
source <route/to/venv-directory>/bin/activate
pip install -r requirements.txt
```

## Running the application

1. Activate the virtual environment: `source venv/bin/activate`
2. Run `python src/main.py`
3. From the browser: `http://localhost:8000`

## Tests

Running the `build.py` script performs several static code analysis and test suites:
- pycodestyle (pep8)
- pylint
- Unit tests
- End-to-end tests

To run:
1. Activate the virtual environment: `source venv/bin/activate`
2. Install dev dependencies: `pip install -r requirements_dev.txt`
3. Run: `PYTHONPATH=src python build.py`

To check coverage, run:
1. `PYTHONPATH=src coverage run --concurrency=multiprocessing build.py`
2. `coverage combine`
3. `coverage html`
4. Open `htmlcov/index.html` in your browser
