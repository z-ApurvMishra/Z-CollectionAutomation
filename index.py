import subprocess
import json
import os
import requests

# Constants
TEMP_COLLECTION_FILE = "temp_collection.json"
REPORT_FILE = "report.json"
HTML_REPORT_FILE = "report.html"
COLLECTION_URL = "URL"  # Replace with your collection URL

# Default tests to add if not present
DEFAULT_TESTS = [
    """pm.test("Response status code is 200", function () {
        pm.expect(pm.response.code).to.equal(200);
    });""",
    """pm.test("Response time is within an acceptable range", function () {
        pm.expect(pm.response.responseTime).to.be.below(500);
    });""",
    """pm.test("Response has the required fields", function () {
        const responseData = pm.response.json();
        pm.expect(responseData).to.be.an('object');
        pm.expect(responseData).to.include.all.keys('success', 'status_code', 'message', 'data', 'patch_data');
    });""",
    """pm.test("Check success value is true", function () {
        const responseData = pm.response.json();
        pm.expect(responseData.success).to.be.true;
    });""",
]


def test_exists(test_string, existing_tests):
    """Checks if a test already exists in the list of tests."""
    return any(test_string.strip() == existing_test.strip() for existing_test in existing_tests)


def add_default_tests(collection_data):
    """Adds default tests to requests in a Postman collection if they don't already exist."""
    for item in collection_data.get('collection', {}).get('item', []):
        # Check for 'event' list and create if it doesn't exist
        if 'event' not in item:
            item['event'] = []

        # Check if a test script already exists
        test_event = next((event for event in item['event'] if event.get('listen') == 'test'), None)

        if not test_event:
            # Create test if one doesn't exists
            test_event = {
                "listen": "test",
                "script": {
                    "exec": [],  # Start with an empty list, we'll add tests later
                    "type": "text/javascript"
                }
            }
            item['event'].append(test_event)

        if 'script' in test_event and 'exec' in test_event['script']:
            existing_tests = test_event['script']['exec']
            for test_block in DEFAULT_TESTS:
                if not test_exists(test_block, existing_tests):
                    print(f"Adding test to item '{item.get('name', 'Unknown')}'")
                    existing_tests.append(test_block)  # Add the entire block as one string

        else:
            print(f"Warning: 'script' or 'exec' missing in item: {item.get('name', 'Unknown Item')}")

    return collection_data


def run_postman_collection(collection_data):
    """Executes a Postman Collection using Newman and generates a JSON report."""

    with open(TEMP_COLLECTION_FILE, "w") as f:
        json.dump(collection_data, f, indent=4)

    command = [
        "newman", "run", TEMP_COLLECTION_FILE,
        "--reporters", "json,html",
        "--reporter-json-export", REPORT_FILE,
        "--reporter-html-export", HTML_REPORT_FILE
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Execution Output:\n", result.stdout)
        print("✅ Postman collection executed successfully!")

    except subprocess.CalledProcessError as e:
        print("❌ Test execution failed!")
        print("Error details:", e.stderr)
    except Exception as e:
        print("❌ Error running Newman:", e)


def analyze_report():
    """Parses the JSON report and prints test results."""

    if not os.path.exists(REPORT_FILE):
        print("❌ Report file not found. Run the collection first.")
        return

    with open(REPORT_FILE, "r") as file:
        data = json.load(file)

    summary = data.get("run", {}).get("stats", {})

    print("\n📊 Test Summary:")
    print(f"Total Requests: {summary.get('requests', {}).get('total', 0)}")
    print(f"Total Assertions: {summary.get('assertions', {}).get('total', 0)}")
    print(f"Passed: {summary.get('assertions', {}).get('total', 0) - summary.get('assertions', {}).get('failed', 0)}")
    print(f"Failed: {summary.get('assertions', {}).get('failed', 0)}")


def get_collection_from_url(collection_url):
    """Downloads the latest Postman collection from the given URL."""
    try:
        response = requests.get(collection_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading collection from {collection_url}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in the collection downloaded from {collection_url}")
        return None


def delete_existing_temp_file():
    """Deletes the temporary collection file if it exists."""
    if os.path.exists(TEMP_COLLECTION_FILE):
        try:
            os.remove(TEMP_COLLECTION_FILE)
            print(f"✅ Existing {TEMP_COLLECTION_FILE} deleted.")
        except OSError as e:
            print(f"⚠️  Error deleting {TEMP_COLLECTION_FILE}: {e}")


if __name__ == "__main__":
    delete_existing_temp_file()

    collection_data = get_collection_from_url(COLLECTION_URL)

    if collection_data:
        updated_collection_data = add_default_tests(collection_data)

        with open("modified_collection.json", "w") as f:
            json.dump(updated_collection_data, f, indent=4)
        print("✅ Modified collection saved to modified_collection.json")

        run_postman_collection(updated_collection_data)
        analyze_report()

    else:
        print("❌ Aborted: Failed to load collection data.")