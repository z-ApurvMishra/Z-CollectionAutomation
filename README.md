# Postman Collection Automation

This project automates the execution of Postman collections with token-based authentication. It handles login, token extraction, and subsequent API requests automatically.

## Features

- Automatic download of Postman collections using API
- Login authentication and token extraction
- Dynamic token injection into requests
- Automated test execution with Newman
- HTML and JSON report generation
- Test assertions for API responses

## Prerequisites

### System Requirements
- Python 3.6 or higher
- Node.js 10 or higher
- npm (Node Package Manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Z-CollectionAutomation
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Newman and HTML reporter**
   ```bash
   npm install -g newman
   npm install -g newman-reporter-html
   ```

4. **Verify installations**
   ```bash
   python --version
   node --version
   newman --version
   ```

## Project Structure

```
Z-CollectionAutomation/
├── index.py              # Main script
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

The script uses two main Postman collection URLs:
- Login Collection: For authentication
- User Collection: For main API operations

These URLs are configured in `index.py` with their respective access keys.

## Usage

Run the script using:
```bash
python index.py
```

The script will:
1. Download the collections from Postman
2. Execute the login collection
3. Extract authentication tokens
4. Update the main collection with tokens
5. Execute the modified collection
6. Generate test reports

## Test Reports

After execution, two report files are generated:
- `report.html`: HTML report with detailed test results
- `report.json`: JSON format report for programmatic analysis

## Test Assertions

Default test assertions include:
- Status code verification (200)
- JSON response validation
- Success field verification

## Error Handling

The script includes comprehensive error handling for:
- Collection download failures
- Authentication failures
- Token extraction issues
- Request execution errors

## Dependencies

### Python Packages
- `requests>=2.31.0`: For HTTP requests
- `python-dateutil>=2.8.2`: For datetime handling
- `newman>=1.0.0`: For running collections

### Node.js Packages
- `newman`: CLI tool for running Postman collections
- `newman-reporter-html`: For HTML report generation

## Troubleshooting

1. **Newman not found**
   ```bash
   npm install -g newman
   ```

2. **HTML reports not generating**
   ```bash
   npm install -g newman-reporter-html
   ```

3. **Permission issues**
   ```bash
   sudo npm install -g newman newman-reporter-html
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]