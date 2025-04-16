import requests
import time
import sys
from requests.exceptions import RequestException

def check_browser_health(base_url):
    """Check if the browser/crawler functionality is working"""
    try:
        # Simple test crawl with minimal configuration
        test_request = {
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {"max_pages": 1}
        }
        response = requests.post(f"{base_url}/crawl", json=test_request)
        response.raise_for_status()
        return True
    except RequestException:
        return False

def test_local_deployment():
    base_url = "http://localhost:18000"
    print("Testing Crawl4AI Docker local deployment")

    # Test basic crawl
    print("\n=== Testing Basic Crawl ===")
    request = {
        #"urls": ["https://www.unionb.com/credit-cards-offers/"],
        "urls": ["https://example.com"],
        "browser_config": {"persistent": True},
        "crawler_config": {}
    }

    try:
        # Submit crawl request
        response = requests.post(f"{base_url}/crawl", json=request)
        response.raise_for_status()
        print("Crawl response:", response.json())
        return True
        
    except RequestException as e:
        print(f"Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    base_url = "http://localhost:18000"
    max_retries = 3
    initial_backoff = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # First check if service is healthy
            health = requests.get(f"{base_url}/health")
            health.raise_for_status()
            print("Health check passed:", health.json())
            
            # Additional check for browser functionality
            print("Checking browser functionality...")
            if not check_browser_health(base_url):
                print("Browser check failed - waiting before retry")
                backoff_time = initial_backoff * (2 ** attempt)  # Exponential backoff
                print(f"Waiting {backoff_time} seconds before retry...")
                time.sleep(backoff_time)
                continue
                
            # Run the test
            if test_local_deployment():
                print("\nTest completed successfully!")
                sys.exit(0)
            else:
                print(f"\nTest failed on attempt {attempt + 1}")
                backoff_time = initial_backoff * (2 ** attempt)
                if attempt < max_retries - 1:
                    print(f"Waiting {backoff_time} seconds before retry...")
                    time.sleep(backoff_time)
                
        except RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                backoff_time = initial_backoff * (2 ** attempt)
                print(f"Waiting {backoff_time} seconds before retry...")
                time.sleep(backoff_time)
            continue
    
    print("\nAll attempts failed")
    sys.exit(1)

    