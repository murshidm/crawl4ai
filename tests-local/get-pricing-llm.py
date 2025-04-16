import subprocess
import requests
import time
import json

COMPOSE_FILE = "docker-compose.yml"
SERVICE_NAME = "crawl4ai-arm64"  # or whichever service you want
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

        # Prepare the request
        url = f"http://localhost:{API_PORT}/crawl"
        headers = {"Content-Type": "application/json"}
        payload = {
            "urls": ["https://cohere.com/pricing"],
            "extraction_strategy": {
                "type": "llm",
                "provider": "openai/gpt-4o",
                "api_token": OPENAI_API_KEY,
                "extraction_type": "schema",
                "schema": {
                    "model_name": "str",
                    "input_fee": "str",
                    "output_fee": "str"
                },
                "instruction": (
                    "From the crawled content, extract all mentioned model names along with their fees for input and output tokens. "
                    "One extracted model JSON format should look like this: "
                    "{\"model_name\": \"GPT-4\", \"input_fee\": \"US$10.00 / 1M tokens\", \"output_fee\": \"US$30.00 / 1M tokens\"}."
                )
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
        with open("crawl_response.json", "w") as f:
            json.dump(result, f, indent=2)

        # Check for error keys in the response
        if "error" in result or response.status_code != 200:
            print("API returned an error or non-200 status code.")
            # Print container logs for debugging
            logs = subprocess.check_output([
                "docker", "compose", "-f", COMPOSE_FILE, "logs", SERVICE_NAME
            ]).decode(errors="ignore")
            print("Container logs:\n", logs)

    except Exception as e:
        result = {"error": str(e)}
        # Print container logs for debugging
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