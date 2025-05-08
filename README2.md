# Crawl4AI for VS Code API Documentation Scraping

This guide covers the full setup process for the VS Code API documentation scraper project from scratch.

## Step 1: Create a Virtual Environment

First, create a Python virtual environment:

```bash
# Create a virtual environment named .venv (hidden directory)
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate
```

## Step 2: Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
# If you already have requirements.txt:
pip install -r requirements.txt
```

## Step 3: Install Playwright Browsers

Playwright needs browser binaries to run properly:

```bash
# Standard installation (sufficient for most Windows/Mac systems):
playwright install

# OR for complete installation with all system dependencies (recommended for Linux/Docker):
# playwright install --with-deps
```

## Step 4: Run the Scraper

Now you can run the script:

```bash
python src/scrape_vscode_api_docs.py
```

## Step 5: Access Your Documentation

After running the script, you'll find the VS Code API documentation saved as Markdown files in the vscode_api_docs directory.

## Complete requirements.txt

Here's the complete requirements.txt file for reference:

```text
crawl4ai>=0.5.0
aiohttp>=3.8.0
beautifulsoup4>=4.10.0
pathlib>=1.0.1
typing-extensions>=4.0.0
playwright>=1.30.0
```

## Notes

- .venv is a common naming convention for virtual environments, especially in modern Python projects, as it's recognized by many IDEs including VS Code
- Playwright's installation involves two parts: the Python package (installed via pip) and the browser binaries (installed via the `playwright install` command)
- The script filters URLs during crawling to stay within the VS Code API documentation section
- Content is saved as Markdown files with a directory structure that mirrors the website's URL structure
