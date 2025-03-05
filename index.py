import subprocess
import json
import os

# Define paths
COLLECTION_FILE = "/Users/macofapurv/Desktop/Collection Automation/Z-Collections.postman_collection.json"
REPORT_FILE = "report.json"
HTML_REPORT_FILE = "report.html"

def update_collection_file(new_exec_code):
    """
    Updates ALL 'exec' parts of the Postman collection file.

    Args:
        new_exec_code (list of strings): The new 'exec' code (list of strings) to replace all existing ones with.
    """

    try:
        with open(COLLECTION_FILE, "r") as f:
            collection_data = json.load(f)

        # Iterate through each item (request) in the collection
        for item in collection_data.get('item', []):
            # Iterate through each event in the item
            for event in item.get('event', []):
                if 'script' in event and 'exec' in event['script']:
                    print(f"Updating 'exec' in item: {item.get('name', 'Unknown Item')}")  # Indicate which item's exec is being updated
                    event['script']['exec'] = new_exec_code

        # Write the updated data back to the file
        with open(COLLECTION_FILE, "w") as f:
            json.dump(collection_data, f, indent=4)  # indent=4 for pretty formatting

        print("✅ Collection file updated successfully!")

    except FileNotFoundError:
        print(f"❌ Error: Collection file not found at {COLLECTION_FILE}")
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in the collection file.")
    except Exception as e:
        print(f"❌ Error updating collection file: {e}")


def run_postman_collection():
    """Executes a Postman Collection using Newman and generates a JSON report."""

    command = [
        "newman", "run", COLLECTION_FILE,
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
        print("Error running Newman:", e)


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

    command = [
        "newman", "run", COLLECTION_FILE,
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
            "pm.test(\"Response time is within an acceptable range\", function () {",
            "  pm.expect(pm.response.responseTime).to.be.below(500);",
            "});",
            "",
            "pm.test(\"Response has the required fields\", function () {",
            "    const responseData = pm.response.json();",
            "    ",
            "    pm.expect(responseData).to.be.an('object');",
            "    pm.expect(responseData).to.include.all.keys('success', 'status_code', 'message', 'data', 'patch_data');",
            "});",
            "",
            "pm.test(\"Access token and refresh token should not be empty strings\", function () {",
            "  const responseData = pm.response.json();",
            "  ",
            "  pm.expect(responseData.data.access_token).to.be.a('string').and.to.have.lengthOf.at.least(1, \"Access token should not be empty\");",
            "  pm.expect(responseData.data.refresh_token).to.be.a('string').and.to.have.lengthOf.at.least(1, \"Refresh token should not be empty\");",
            "});",
            ""
    ]

    update_collection_file(new_exec_code)  # Update the collection file
    run_postman_collection()
    analyze_report()
    generate_html_report()