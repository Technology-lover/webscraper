import argparse
import json
import os
import sys
from bs4 import BeautifulSoup


def parse_html_content(filepath: str) -> dict:
    """Safely reads and parses a single HTML file into a dictionary."""
    data = {
        "source_file": os.path.basename(filepath),
        "title": None,
        "headings": [],
        "links": [],
        "paragraphs": [],
        "status": "success",
        "error": None
    }

    try:
        # Prevent crash on missing or unreadable files
        if not os.path.isfile(filepath):
            data["status"] = "error"
            data["error"] = "File not found"
            return data

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Fallback to standard html.parser if lxml isn't installed
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        # Safely extract title
        if soup.title and soup.title.string:
            data["title"] = soup.title.string.strip()

        # Safely extract headings
        for h in soup.find_all(["h1", "h2", "h3"]):
            text = h.get_text(strip=True)
            if text:
                data["headings"].append(text)

        # Safely extract links
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href:
                data["links"].append(href)

        # Safely extract paragraphs
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                data["paragraphs"].append(text)

    except Exception as e:
        # Catch unexpected memory/parsing errors per file
        data["status"] = "error"
        data["error"] = str(e)

    return data


def output_stdout(results: list) -> None:
    """Prints extracted content to terminal stdout."""
    for res in results:
        print(f"=== File: {res['source_file']} ===")
        if res["status"] == "error":
            print(f"Error: {res['error']}\n")
            continue

        print(f"Title: {res['title']}")
        print(f"Headings Count: {len(res['headings'])}")
        print(f"Links Count: {len(res['links'])}")
        print(f"Paragraphs Count: {len(res['paragraphs'])}")
        print("-" * 50)


def output_json(results: list, output_filename: str) -> None:
    """Saves or appends parsed data to a JSON file safely."""
    try:
        existing_data = []
        if os.path.exists(output_filename):
            try:
                with open(output_filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []

        existing_data.extend(results)

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully saved/updated JSON output: {output_filename}")

    except Exception as e:
        print(f"Failed to write JSON output: {e}", file=sys.stderr)


def output_txt(results: list, output_filename: str) -> None:
    """Appends structured text results to a .txt file."""
    try:
        with open(output_filename, "a", encoding="utf-8") as f:
            for res in results:
                f.write(f"=== File: {res['source_file']} ===\n")
                if res["status"] == "error":
                    f.write(f"Status: ERROR ({res['error']})\n\n")
                    continue

                f.write(f"Title: {res['title']}\n")
                f.write("Headings:\n")
                for h in res["headings"]:
                    f.write(f"  - {h}\n")
                f.write("Links:\n")
                for link in res["links"]:
                    f.write(f"  - {link}\n")
                f.write("\n" + "=" * 50 + "\n\n")

        print(f"Successfully appended text output: {output_filename}")

    except Exception as e:
        print(f"Failed to write TXT output: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Parse HTML files using BeautifulSoup safely."
    )

    # Accept one or multiple file paths from command line
    parser.add_argument(
        "files",
        nargs="+",
        help="Path to one or more HTML files to parse."
    )

    # Optional output flags
    parser.add_argument(
        "--json",
        nargs="?",
        const="parsed_output.json",
        default=None,
        metavar="OUTPUT_FILE",
        help="Save output in JSON format (default: parsed_output.json)"
    )

    parser.add_argument(
        "--txt",
        nargs="?",
        const="parsed_output.txt",
        default=None,
        metavar="OUTPUT_FILE",
        help="Save output in TXT format (default: parsed_output.txt)"
    )

    args = parser.parse_args()

    # Process files
    results = []
    for filepath in args.files:
        parsed_data = parse_html_content(filepath)
        results.append(parsed_data)

    # Route output based on command line flags
    if args.json:
        output_json(results, args.json)

    if args.txt:
        output_txt(results, args.txt)

    # Default to stdout if no export flags were passed
    if not args.json and not args.txt:
        output_stdout(results)


if __name__ == "__main__":
    main()
