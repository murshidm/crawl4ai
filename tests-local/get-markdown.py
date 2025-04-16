import subprocess
import requests
import time
import json

COMPOSE_FILE = "docker-compose.yml"
SERVICE_NAME = "crawl4ai-arm64" #amd64 for Ubuntu
API_PORT = 18000

def run_compose_up():
    subprocess.run([
        "docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--wait", SERVICE_NAME
    ], check=True)

def run_compose_down():
    subprocess.run([
        "docker", "compose", "-f", COMPOSE_FILE, "down"
    ], check=True)

def wait_for_api(port, timeout=120):
    url = f"http://localhost:{port}/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

def main():
    result = {}
    try:
        print("Bringing up the service with docker compose...")
        run_compose_up()
        print("Waiting for API to become healthy...")
        if not wait_for_api(API_PORT):
            result = {"error": "API did not become healthy in time."}
            print(json.dumps(result, indent=2))
            # Print container logs for debugging
            logs = subprocess.check_output([
                "docker", "compose", "-f", COMPOSE_FILE, "logs", SERVICE_NAME
            ]).decode(errors="ignore")
            print("Container logs:\n", logs)
            return

        # Prepare the request for basic markdown crawl (official schema)
        url = f"http://localhost:{API_PORT}/crawl"
        headers = {"Content-Type": "application/json"}
        payload = {
            "urls": ["https://news.ycombinator.com/"],
            "browser_config": {
                "type": "BrowserConfig",
                "params": {
                    "headless": True
                }
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    # You can add more config here if needed, e.g. markdown_generator, cache_mode, etc.
                }
            }
        }

        print("Sending POST request to /crawl endpoint...")
        print("Request payload:", json.dumps(payload, indent=2))
        response = requests.post(url, headers=headers, json=payload)
        print("Status code:", response.status_code)
        print("Response text (first 100 chars):", response.text[:100])

        try:
            result = response.json()
        except Exception:
            result = {"error": "Non-JSON response", "content": response.text}

        # Save the full response to a JSON file
        with open("tests-local/crawl_hn_markdown_response.json", "w") as f:
            json.dump(result, f, indent=2)

        # Try to print the first 100 chars of markdown if present
        try:
            markdown = None
            if isinstance(result, dict):
                if "markdown" in result:
                    markdown = result["markdown"]
                elif "results" in result and isinstance(result["results"], list) and result["results"]:
                    res0 = result["results"][0]
                    if "markdown" in res0:
                        markdown = res0["markdown"]
                    elif "markdown" in res0.get("output", {}):
                        markdown = res0["output"]["markdown"]
            if markdown:
                print("First 100 chars of markdown:", markdown[:100])
            else:
                print("Markdown not found in response.")
        except Exception as e:
            print("Error extracting markdown from response:", str(e))

        # Check for error keys in the response
        if "error" in result or response.status_code != 200:
            print("API returned an error or non-200 status code.")
            logs = subprocess.check_output([
                "docker", "compose", "-f", COMPOSE_FILE, "logs", SERVICE_NAME
            ]).decode(errors="ignore")
            print("Container logs:\n", logs)

    except Exception as e:
        result = {"error": str(e)}
        try:
            logs = subprocess.check_output([
                "docker", "compose", "-f", COMPOSE_FILE, "logs", SERVICE_NAME
            ]).decode(errors="ignore")
            print("Container logs:\n", logs)
        except Exception:
            pass
    finally:
        print("Bringing down the service with docker compose...")
        run_compose_down()
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()