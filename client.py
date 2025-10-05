import argparse
import os
import sys

import requests

def download_file(url, directory):
    try:
        os.makedirs(directory, exist_ok=True)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        if url.endswith("/"):
            filename = "index.html"
        else:
            filename = os.path.basename(url) or "index.html"

        content_type = response.headers.get("Content-type", "").lower()

        if content_type.startswith("text/html"):
            print("\nBody of the response:")
            print(response.text)
            file_path = os.path.join(directory, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"HTML file saved: {file_path}")


        elif content_type.startswith("image/png") or content_type.startswith("application/pdf"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"File saved: {file_path}")

        else:
            print(f"Unsupported content type: {content_type}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='HTTP Client for file server')
    parser.add_argument('server_host', help='Server hostname or IP')
    parser.add_argument('server_port', type=int, help='Server port number')
    parser.add_argument('filename', help='Filename or path to download')
    parser.add_argument('save_directory', help='Directory to save files in')

    args = parser.parse_args()

    url = f"http://{args.server_host}:{args.server_port}/view/{args.filename}"

    print(f"Downloading: {url}")
    print(f"Saving to directory: {args.save_directory}")
    download_file(url, args.save_directory)

if __name__ == "__main__":
    main()