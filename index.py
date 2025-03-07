import subprocess
import json
import os
import requests
from datetime import datetime

# Constants
TEMP_COLLECTION_FILE = "temp_collection.json"
REPORT_FILE = "report.json"
HTML_REPORT_FILE = "report.html"

# Collection URLs with their respective access keys
LOGIN_COLLECTION_URL = "URL_One"
USER_COLLECTION_URL = "URL_Two"

# Default test assertions
DEFAULT_TESTS = [
    "pm.test('Status code is 200', function() {",
    "    pm.response.to.have.status(200);",
    "});",
    "",
    "pm.test('Response is valid JSON', function() {",
    "    pm.response.to.be.json;",
    "});",
    "",
    "pm.test('Response has success field', function() {",
    "    var jsonData = pm.response.json();",
    "    pm.expect(jsonData).to.have.property('success');",
    "    pm.expect(jsonData.success).to.be.true;",
    "});"
]

def download_collection(collection_url):
    """Downloads a collection from Postman API."""
    try:
        print(f"\n=== Downloading collection from URL ===")
        print(f"URL: {collection_url}")
        
        response = requests.get(collection_url)
        response.raise_for_status()
        
        collection_data = response.json()
        collection_name = collection_data.get('collection', {}).get('info', {}).get('name', 'collection')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{collection_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(collection_data, f, indent=4)
        
        print(f"✅ Collection downloaded and saved as {filename}")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading collection: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response details: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

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


def run_postman_collection(collection_file):
    """Run Postman collection using Newman."""
    print("\n=== Running Newman Command ===")
    command = [
        "newman",
        "run",
        collection_file,
        "--reporters", "cli,json,html",
        "--reporter-json-export", "report.json",
        "--reporter-html-export", "report.html",
        "--verbose"
    ]
    print("Command:", " ".join(command))
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print("\n=== Newman Execution Output ===")
        print(result.stdout)
        print("\n=== Newman Error Output ===")
        print(result.stderr)
        
        # Check if report files were created
        if os.path.exists("report.json"):
            with open("report.json", "r") as f:
                report_content = f.read()
            print("\n=== Checking Report Files ===")
            print("✅ Report file created: report.json")
            print(f"Report contains {len(report_content)} characters")
        else:
            print("❌ Report file not created")
            
        if os.path.exists("report.html"):
            print("✅ HTML report created: report.html")
        else:
            print("❌ HTML report not created")
            
        if result.returncode == 0:
            print("\n✅ Postman collection executed successfully!")
            return True
        else:
            print("\n❌ Test execution failed!")
            print("Error details:", result.stderr)
            return False
            
    except Exception as e:
        print(f"\n❌ Error running Newman: {e}")
        return False


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


def extract_tokens_from_output(newman_output):
    """Extracts access_token and refresh_token from Newman output."""
    if not newman_output:
        print("❌ No Newman output to extract tokens from.")
        return None, None

    try:
        print("\n=== Attempting to extract tokens ===")
        
        # Find the response body section
        response_sections = newman_output.split('┌ ↓ application/json')
        if len(response_sections) < 2:
            print("❌ Could not find response body section.")
            return None, None
            
        response_body = response_sections[1].split('└')[0].strip()
        if not response_body:
            print("❌ Response body is empty.")
            return None, None
            
        # Clean up the response body string
        # Remove the header line and any leading/trailing whitespace
        response_lines = response_body.split('\n')
        if len(response_lines) < 2:
            print("❌ Response body is malformed.")
            return None, None
            
        # Join the lines and remove any leading/trailing whitespace and pipe characters
        response_body = ''.join(response_lines[1:]).strip()
        response_body = response_body.replace('│', '').strip()
        
        try:
            response_data = json.loads(response_body)
            print("✅ Successfully parsed response data")
            
            # Extract tokens
            access_token = response_data.get('data', {}).get('access_token')
            refresh_token = response_data.get('data', {}).get('refresh_token')

            if not access_token or not refresh_token:
                print("❌ Could not find tokens in response data.")
                print("Available keys in response:", list(response_data.keys()))
                if 'data' in response_data:
                    print("Available keys in data:", list(response_data['data'].keys()))
                return None, None

            print("✅ Successfully extracted tokens")
            return access_token, refresh_token
            
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding response body: {e}")
            print("Cleaned response body:", response_body[:200] + "...")
            return None, None
            
    except Exception as e:
        print(f"❌ Error extracting tokens: {e}")
        return None, None


def clean_cookie_value(cookie_value):
    """Clean up cookie value by removing extra spaces and line breaks."""
    return ' '.join(cookie_value.split())


def update_request_headers(request, access_token, refresh_token):
    """Update request headers with new tokens."""
    if 'header' not in request:
        request['header'] = []
        
    # Find or create Cookie header
    cookie_header = next((h for h in request['header'] if h['key'] == 'Cookie'), None)
    if not cookie_header:
        cookie_header = {'key': 'Cookie', 'value': ''}
        request['header'].append(cookie_header)
    
    # Update cookie value with new tokens
    cookie_value = f"account_id=514; central_jwt_token={access_token}; central_jwt_refresh_token={refresh_token}"
    cookie_header['value'] = clean_cookie_value(cookie_value)


def add_tests_to_request(item):
    """Adds test scripts to a request if they don't exist."""
    if 'event' not in item:
        item['event'] = []
    
    # Check if a test script already exists
    test_event = next((event for event in item['event'] if event.get('listen') == 'test'), None)
    
    if not test_event:
        # Create test if one doesn't exist
        test_event = {
            "listen": "test",
            "script": {
                "exec": DEFAULT_TESTS,
                "type": "text/javascript"
            }
        }
        item['event'].append(test_event)
        print(f"✅ Added tests to request '{item.get('name', 'Unknown')}'")
    else:
        print(f"ℹ️  Tests already exist for request '{item.get('name', 'Unknown')}'")


def modify_collection(collection_data, access_token, refresh_token):
    """Modify collection with new tokens and add tests."""
    print("\n=== Modifying collection with new tokens and tests ===")
    
    # Update host_name in login request
    login_request = next((item for item in collection_data['collection']['item'] if item['name'] == 'Login'), None)
    if login_request:
        login_request['request']['body']['raw'] = login_request['request']['body']['raw'].replace(
            '"host_name": "<string>"',
            '"host_name": "qa2.zenarate.com"'
        )
        print("✅ Updated host_name in login request")
    
    # Update tokens and add tests to all requests
    for item in collection_data['collection']['item']:
        print(f"Processing request '{item['name']}'")
        update_request_headers(item['request'], access_token, refresh_token)
        add_tests_to_request(item)
    
    # Save modified collection
    with open('modified_collection.json', 'w') as f:
        json.dump(collection_data, f, indent=4)
    print("✅ Modified collection saved to modified_collection.json")


def main():
    """Main function to run the collection automation."""
    # Download collections
    login_collection_file = download_collection(LOGIN_COLLECTION_URL)
    if not login_collection_file:
        print("❌ Failed to download login collection")
        return
    
    user_collection_file = download_collection(USER_COLLECTION_URL)
    if not user_collection_file:
        print("❌ Failed to download user collection")
        return
    
    # Run login collection
    if not run_postman_collection(login_collection_file):
        print("❌ Failed to run login collection")
        return
    
    # Extract tokens from output
    access_token, refresh_token = extract_tokens_from_output(subprocess.check_output(['newman', 'run', login_collection_file, '--verbose'], text=True))
    if not access_token or not refresh_token:
        print("❌ Failed to obtain tokens")
        return
    
    print("✅ Successfully obtained tokens.")
    
    # Load main collection
    with open(user_collection_file, 'r') as f:
        collection_data = json.load(f)
    
    # Modify collection with new tokens
    modify_collection(collection_data, access_token, refresh_token)
    
    # Run modified collection
    if not run_postman_collection('modified_collection.json'):
        print("❌ Failed to run modified collection")
        return
    
    # Clean up downloaded files
    try:
        os.remove(login_collection_file)
        os.remove(user_collection_file)
        print("\n✅ Cleaned up downloaded collection files")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not clean up files: {e}")
    
    print("\n✅ Collection automation completed successfully!")


if __name__ == "__main__":
    main()