# Filename: scrape_page_to_markdown.py
"""
Scrapes a single web page URL provided by the user and saves its
content as a Markdown file.

Features:
- Automatically suggests a filename based on the URL.
- Prompts the user to confirm or change the filename.
- Handles existing files by prompting to Overwrite, Rename, or Abort.
"""

import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys
import os # Needed for path manipulation

# --- Dependency Check ---
try:
    # Ensure you have installed crawl4ai: pip install crawl4ai
    # You might also need to run `crawl4ai-setup` or `playwright install --with-deps`
    # once in your terminal to install necessary browser components.
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
except ImportError as e:
    print(f"[ERROR] Missing required library: {e}")
    print("Please install Crawl4AI and its dependencies:")
    print("  pip install crawl4ai")
    print("Then run the setup command in your terminal:")
    print("  crawl4ai-setup")
    print("Or alternatively:")
    print("  playwright install --with-deps")
    sys.exit(1)
# --- End Dependency Check ---

# --- Configuration ---
# Set to False to reduce Crawl4AI's console logging
VERBOSE_LOGGING = True
# --- End Configuration ---


def sanitize_filename(name: str) -> str:
    """Removes invalid characters and cleans up a potential filename."""
    # Remove characters invalid for Windows/Linux/MacOS filenames
    # Keep alphanumeric, underscore, hyphen, dot. Replace others with underscore.
    safe_name = re.sub(r'[<>:"/\\|?*\s]+', '_', name)
    # Replace multiple consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Remove leading/trailing underscores/dots
    safe_name = safe_name.strip('._')
    # Limit length to prevent issues
    safe_name = safe_name[:150]
    if not safe_name: # Handle case where sanitization results in empty string
        return "scraped_page"
    return safe_name

def generate_default_filename(url: str) -> str:
    """Generates a default .md filename from a URL."""
    try:
        parsed = urlparse(url)
        # Get the path part, remove leading/trailing slashes, decode % encoding
        path_part = unquote(parsed.path.strip('/'))

        if not path_part: # Handle root URL or path ending in /
            # Use domain name or a default if domain is also missing
            name = parsed.netloc.replace('.', '_') if parsed.netloc else 'scraped_page'
        else:
            # Get last path segment
            name = path_part.split('/')[-1]
            # If the last segment was empty (e.g. trailing slash), try the one before it
            if not name and len(path_part.split('/')) > 1:
                name = path_part.split('/')[-2]
            # Fallback if name is still empty
            if not name:
                name = parsed.netloc.replace('.', '_') if parsed.netloc else 'scraped_page'


        # Remove existing extension if present (e.g. .html) before sanitizing
        name_base, _ = os.path.splitext(name)
        safe_name = sanitize_filename(name_base)
        # Ensure it ends with .md
        if not safe_name.lower().endswith(".md"):
            return safe_name + ".md"
        else:
            # If sanitizing somehow resulted in ending with .md (unlikely but possible)
            return safe_name
    except Exception as e:
        print(f"[WARN] Error generating filename from URL '{url}': {e}")
        return "scraped_page.md" # Fallback filename

async def main():
    """Main function to get URL, filename, handle conflicts, crawl, and save."""
    url = input("Enter the URL you want to crawl: ").strip()
    if not url:
        print("URL cannot be empty.")
        return

    default_filename = generate_default_filename(url)

    # Loop to get a valid filename confirmation or input
    while True:
        chosen_filename_str = input(f"Enter the output filename (default: {default_filename}): ").strip()
        if not chosen_filename_str:
            chosen_filename_str = default_filename
            print(f"Using default: {chosen_filename_str}") # Confirm default usage
            break # Exit loop using default
        # Basic check if filename seems plausible (not empty after strip)
        elif chosen_filename_str:
            # Ensure .md extension if user provided name without it
            if not chosen_filename_str.lower().endswith(".md"):
                chosen_filename_str += ".md"
            break # Exit loop using user input
        else:
            print("Filename cannot be empty if not using default. Please try again.")


    output_path = Path(chosen_filename_str)

    # Handle file existence with overwrite/rename/abort options
    while output_path.exists():
        action = input(f"File '{output_path}' already exists. Overwrite (o), Rename (r), Abort (a)? ").strip().lower()
        if action == 'o':
            print(f"Will overwrite '{output_path}'.")
            break # Proceed with overwriting
        elif action == 'a':
            print("Operation aborted.")
            return # Exit the script
        elif action == 'r':
            counter = 1
            base = output_path.stem # File name without extension
            ext = output_path.suffix # File extension (e.g., '.md')
            while True:
                # Suggest a new name like base_1.md, base_2.md, etc.
                new_name = f"{base}_{counter}{ext}"
                new_path = Path(new_name)
                if not new_path.exists():
                    output_path = new_path
                    print(f"Will save as '{output_path}' instead.")
                    break # Found a non-existing name
                counter += 1
            break # Break the outer while loop after finding a new name
        else:
            print("Invalid choice. Please enter 'o', 'r', or 'a'.")

    # --- Crawl Logic ---
    print("-" * 30)
    print(f"Starting crawl for: {url}")
    # Configure for single-page crawl (no deep crawling strategy needed)
    # *** FIX: Removed max_depth=0 from CrawlerRunConfig constructor ***
    config = CrawlerRunConfig(verbose=VERBOSE_LOGGING)
    markdown_content = None
    try:
        async with AsyncWebCrawler() as crawler:
            # Use arun for single page crawl
            results = await crawler.arun(url, config=config)
            # Check if results list is not empty and the first result is valid
            if results and results[0].success and results[0].markdown:
                markdown_content = results[0].markdown
                print(f"Successfully scraped content from {url}")
            elif results:
                print(f"[ERROR] Failed to scrape page. Status: {results[0].status_code}, Error: {results[0].error}")
            else:
                print("[ERROR] No results returned from crawler.")

    except Exception as e:
        print(f"[ERROR] An error occurred during crawling: {e}")
        return
    # --- End Crawl Logic ---

    # --- Save Logic ---
    if markdown_content:
        try:
            # Ensure parent directory exists before writing
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Write the scraped content to the final chosen file path
            output_path.write_text(markdown_content, encoding='utf-8', errors='replace')
            print(f"Successfully saved Markdown to '{output_path}'")
        except OSError as e:
            # Catch specific file system errors during write
            print(f"[ERROR] Could not write to file '{output_path}': {e}")
        except Exception as e:
             # Catch any other unexpected errors during saving
             print(f"[ERROR] An unexpected error occurred during saving: {e}")
    else:
        print("No Markdown content was scraped, nothing to save.")
    # --- End Save Logic ---

    print("-" * 30)


if __name__ == "__main__":
    # It's recommended to run `crawl4ai-setup` or `playwright install --with-deps`
    # once manually in your terminal before running this script for the first time.
    asyncio.run(main())
