import subprocess
import json
import os
import requests  # Import the requests library

# Define paths
#COLLECTION_FILE = "/Users/macofapurv/Desktop/Collection Automation/Z-Collections.postman_collection.json" # Local file
COLLECTION_URL = "YOUR_COLLECTION_URL_HERE"  # URL to your Postman collection (e.g., a raw GitHub file, Postman API)
REPORT_FILE = "report.json"
HTML_REPORT_FILE = "report.html"


def get_latest_collection(collection_url):
    """
    Downloads the latest Postman collection from the given URL.

    Returns:
        dict: The JSON data of the collection, or None if there was an error.
    """
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


def update_collection_file(collection_data, new_exec_code):
    """
    Updates ALL 'exec' parts of the provided Postman collection data.

    Args:
        collection_data (dict): The JSON data of the Postman collection.
        new_exec_code (list of strings): The new 'exec' code (list of strings) to replace all existing ones with.
    """

    try:
        # Iterate through each item (request) in the collection
        for item in collection_data.get('item', []):
            # Iterate through each event in the item
            for event in item.get('event', []):
                if 'script' in event and 'exec' in event['script']:
                    print(f"Updating 'exec' in item: {item.get('name', 'Unknown Item')}")  # Indicate which item's exec is being updated
                    event['script']['exec'] = new_exec_code

        print("✅ Collection data updated in memory.")  # Updated in memory, not to file

    except Exception as e:
        print(f"❌ Error updating collection data: {e}")
        return None  # Indicate failure

    return collection_data  # Return the updated collection data


def run_postman_collection(collection_data):
    """Executes a Postman Collection using Newman and generates a JSON report, using in-memory collection data."""

    # Create a temporary file to hold the collection data
    with open("temp_collection.json", "w") as f:
        json.dump(collection_data, f, indent=4)  # Write the JSON to the temp file

    command = [
        "newman", "run", "temp_collection.json",  # Run Newman against the temp file
        "--reporters", "json",
        "--reporter-json-export", REPORT_FILE
    ]

    try:
        # Run the command and capture the output
        result = subprocess.run(command, capture_output=True, text=True, check=True)  # Added check=True
        print("Execution Output:\n", result.stdout)
        print("✅ Postman collection executed successfully!")

    except subprocess.CalledProcessError as e:
        print("❌ Test execution failed!")
        print("Error details:", e.stderr)  # Print standard error for debugging
    except Exception as e:
        print("❌ Error running Newman:", e)
    finally:
        # Clean up the temporary file
        try:
            os.remove("temp_collection.json")
            print("✅ Temporary collection file removed.")
        except OSError as e:
            print(f"⚠️  Error deleting temporary file: {e}") #Non-critical error

def analyze_report():
    """Parses the JSON report and prints test results."""

    if not os.path.exists(REPORT_FILE):
        print("❌ Report file not found. Run the collection first.")
        return

    with open(REPORT_FILE, "r") as file:
        data = json.load(file)

    # Extract summary
    summary = data.get("run", {}).get("stats", {})

    print("\n📊 Test Summary:")
    print(f"Total Requests: {summary.get('requests', {}).get('total', 0)}")
    print(f"Total Assertions: {summary.get('assertions', {}).get('total', 0)}")
    print(f"Passed: {summary.get('assertions', {}).get('total', 0) - summary.get('assertions', {}).get('failed', 0)}")
    print(f"Failed: {summary.get('assertions', {}).get('failed', 0)}")


def generate_html_report():
    """Generates an HTML report from the collection run."""

    # The command will use the last used collection file(temp_collection.json)
    command = [
        "newman", "run", "temp_collection.json",  #Fixed: using temp_collection.json
        "--reporters", "html",
        "--reporter-html-export", HTML_REPORT_FILE
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ HTML report generated: {HTML_REPORT_FILE}")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to generate HTML report:", e)

if __name__ == "__main__":
    # Define the new 'exec' code to use for ALL 'exec' blocks
    new_exec_code = [
        "pm.test(\"Response status code is 200\", function () {",
        "  pm.expect(pm.response.code).to.equal(200);",
        "});",
        "",
        "pm.test(\"New generic assertion\", function() {",
        "  // Add your generic test logic here",
        "  pm.expect(true).to.be.true; // Example assertion",
        "});"
    ]

    # 1. Get the latest collection from the URL
    collection_data = get_latest_collection(COLLECTION_URL)

    if collection_data:
        # 2. Update the collection data (in memory)
        updated_collection_data = update_collection_file(collection_data, new_exec_code)

        if updated_collection_data:
            # 3. Run the Postman collection using the updated data
            run_postman_collection(updated_collection_data) #pass the collection data to the run_postman_collection
            analyze_report()
            generate_html_report()
        else:
            print("❌ Aborted: Failed to update collection data.")
    else:
        print("❌ Aborted: Failed to retrieve collection.")