#macbook
docker compose --profile local-arm64 build --no-cache
docker compose --profile local-arm64 up  # for Apple Silicon

#ubuntu
docker compose --profile local-amd64 build --no-cache
docker compose --profile local-amd64 up  # for Intel


#links
http://localhost:8000/docs
http://localhost:8000/health


#Original Port Usage:
8000 - Main FastAPI application (handles all API endpoints)
8080 - Web interface
9222 - Debug port (likely for browser debugging)
11235 - Currently only used in Docker healthcheck (but nothing is actually listening here)
6379 - Redis server (internal, not exposed)

#Changed port usage
- "18000:8000" # Changed from 8000:8000
- "19222:9222" # Changed from 9222:9222
- "18080:8080" # Changed from 8080:8080
Removed 11235

#Documentation update
import requests

# Submit a crawl job
response = requests.post(
    "http://localhost:18000/crawl",  # Updated from 11235 to 18000
    json={"urls": "https://example.com", "priority": 10}
)
task_id = response.json()["task_id"]

# Continue polling until the task is complete
result = requests.get(f"http://localhost:18000/task/{task_id}")  # Updated from 11235 to 18000