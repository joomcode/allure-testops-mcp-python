# Allure TestOps MCP Server (Python)

Model Context Protocol server for Allure TestOps API, written in Python.

## Overview

This MCP server provides a Python implementation for interacting with Allure TestOps API through the Model Context Protocol. It supports full CRUD operations for test cases, launches, and test plans, along with 56+ controller endpoints for comprehensive Allure TestOps integration.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd allure_testops/mcp/python
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (see Configuration section below)

## Configuration

Set the following environment variables:

- `ALLURE_TESTOPS_URL`: Base URL of your Allure TestOps instance (e.g., `https://your-allure-instance.com`)
- `ALLURE_TOKEN`: API token for authentication (generate in Allure TestOps user settings)
- `PROJECT_ID`: Default project ID (numeric string, e.g., `"1"`)

### Using Environment Variables

```bash
export ALLURE_TESTOPS_URL='https://your-allure-instance.com'
export ALLURE_TOKEN='your-api-token'
export PROJECT_ID='1'
```

### Using .env File (Recommended)

Create a `.env` file in the project root:

```env
ALLURE_TESTOPS_URL=https://your-allure-instance.com
ALLURE_TOKEN=your-api-token
PROJECT_ID=1
MCP_TRANSPORT=stdio
MCP_ADDRESS=0.0.0.0:8000
```

**Note:** Never commit `.env` files to version control. Use `.env.example` as a template.

## Usage

### Running the MCP Server

#### Stdio Mode (Default)

Run the server in stdio mode (default):

```bash
python index.py
# or explicitly:
python index.py --transport stdio
```

The server will run on stdio and communicate via the Model Context Protocol.

#### HTTP Streamable Mode

Run the server in HTTP Streamable mode using environment variables:

```bash
export MCP_TRANSPORT=streamable_http
export MCP_ADDRESS=0.0.0.0:8000
python index.py
```

The server will be available at `http://localhost:8000` (or the specified address).

### Environment Variables

- `MCP_TRANSPORT`: Transport mode (`stdio` or `streamable_http`). Default: `stdio`
- `MCP_ADDRESS`: Host and port in format `host:port`. Default: `0.0.0.0:8000`

### Standalone Scripts

The repository includes utility scripts:

- `get_open_launches.py` - Fetch all open launches from Allure TestOps

```bash
python get_open_launches.py
```

## MCP Configuration

Add to your `mcp.json` (typically located in `~/.cursor/mcp.json` or similar):

```json
{
  "mcpServers": {
    "allure-testops-python": {
      "command": "python3",
      "args": [
        "/absolute/path/to/index.py"
      ],
      "env": {
        "ALLURE_TESTOPS_URL": "https://your-allure-instance.com",
        "ALLURE_TOKEN": "your-api-token",
        "PROJECT_ID": "1"
      }
    }
  }
}
```

## Available Tools

The server provides 10 tools organized by resource type and operation category.

### Test Cases
- `test_case_read` - Read test case data
  - **method="list"** - List all test cases in a project with pagination
  - **method="get"** - Get a specific test case by ID (includes scenario/steps)
- `test_case_write` - Create, update, or delete test cases
  - **method="create"** - Create a new test case
  - **method="update"** - Update an existing test case
  - **method="delete"** - Delete a test case
- `test_case_step_create` - Create a test case step
  - Supports text steps and attachment steps
  - Can insert step before/after specific step ID
  - Optional expected result section

### Launches
- `launch_read` - Read launch data
  - **method="list"** - List all launches in a project with pagination
  - **method="get"** - Get a specific launch by ID
- `launch_write` - Create, update, delete, or close launches
  - **method="create"** - Create a new launch
  - **method="update"** - Update an existing launch
  - **method="delete"** - Delete a launch
  - **method="close"** - Close a launch

### Test Plans
- `test_plan_read` - Read test plan data
  - **method="list"** - List all test plans in a project with pagination
  - **method="get"** - Get a specific test plan by ID
- `test_plan_write` - Create, update, or delete test plans
  - **method="create"** - Create a new test plan
  - **method="update"** - Update an existing test plan
  - **method="delete"** - Delete a test plan

### Special Operations
- `bulk_create_test_cases_from_csv` - Bulk create test cases from CSV content
- `test_case_custom_fields` - Get or modify custom field values
  - **method="get"** - Get custom field values for a test case
  - **method="modify"** - Add or remove a custom field value (with mode="add" or mode="delete")
- `get_custom_field_values` - Get possible values for a custom field in a project
- `test_case_comments` - Get or create comments for a test case
  - **method="get"** - Get comments for a test case with pagination
  - **method="create"** - Create a new comment

## Usage Examples

### Reading Test Cases

```json
// List all test cases in a project
{
  "tool": "test_case_read",
  "arguments": {
    "method": "list",
    "project_id": "1",
    "page": 0,
    "size": 10
  }
}

// Get a specific test case
{
  "tool": "test_case_read",
  "arguments": {
    "method": "get",
    "id": 12345
  }
}
```

### Creating/Updating Resources

```json
// Create a new test case
{
  "tool": "test_case_write",
  "arguments": {
    "method": "create",
    "project_id": "1",
    "name": "Test Login Functionality",
    "description": "Verify user can log in",
    "automated": true
  }
}

// Update a launch
{
  "tool": "launch_write",
  "arguments": {
    "method": "update",
    "id": 67890,
    "name": "Sprint 24 Regression",
    "closed": false
  }
}
```

### Creating Test Case Steps

```json
// Create a simple text step
{
  "tool": "test_case_step_create",
  "arguments": {
    "test_case_id": 7476,
    "text": "Open the login page"
  }
}

// Create a step after a specific step ID
{
  "tool": "test_case_step_create",
  "arguments": {
    "test_case_id": 7476,
    "text": "Enter valid credentials",
    "after_id": 20233
  }
}

// Create a step with expected result
{
  "tool": "test_case_step_create",
  "arguments": {
    "test_case_id": 7476,
    "text": "Click login button",
    "with_expected_result": true
  }
}

// Create a step with custom body_json structure
{
  "tool": "test_case_step_create",
  "arguments": {
    "test_case_id": 7476,
    "body_json": {
      "type": "doc",
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Custom formatted step"
            }
          ]
        }
      ]
    }
  }
}
```

### Custom Fields

```json
// Get custom fields for a test case
{
  "tool": "test_case_custom_fields",
  "arguments": {
    "method": "get",
    "test_case_id": 12345,
    "project_id": "1"
  }
}

// Add a custom field value
{
  "tool": "test_case_custom_fields",
  "arguments": {
    "method": "modify",
    "test_case_id": 12345,
    "project_id": "1",
    "custom_field_id": 100,
    "custom_field_value_id": 200,
    "mode": "add"
  }
}
```

### Comments

```json
// Get comments for a test case
{
  "tool": "test_case_comments",
  "arguments": {
    "method": "get",
    "test_case_id": 7476,
    "page": 0,
    "size": 25
  }
}

// Create a new comment
{
  "tool": "test_case_comments",
  "arguments": {
    "method": "create",
    "test_case_id": 7476,
    "body": "This is a test comment"
  }
}
```

## Features

- ✅ Full Allure TestOps API integration
- ✅ 56+ controller endpoints
- ✅ Async/await support for high performance
- ✅ Type-safe tool definitions
- ✅ Comprehensive error handling
- ✅ CSV import support for bulk operations
- ✅ Clean read/write operation separation

## Project Structure

```
.
├── index.py                 # Main MCP server entry point
├── allure_client.py         # HTTP client for Allure TestOps API
├── csv_parser.py           # CSV parsing utilities
├── controllers/            # API controller modules
├── get_open_launches.py   # Utility script for fetching open launches
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Development

### Testing

Run the test scripts:

```bash
python test_simple.py
python test_mcp.py
```

See `TESTING.md` and `QUICK_TEST.md` for more details.

## Security Notes

- **Never commit API tokens or credentials** to version control
- Use environment variables or secure secret management
- The `.gitignore` file excludes sensitive files by default
- Rotate API tokens regularly

## Contributing

Contributions are welcome! Please ensure:

1. Code follows Python best practices
2. All tests pass
3. No sensitive data is included in commits
4. README is updated for new features

## License

See LICENSE file for details.

## Support

For issues and questions:
- Check the documentation in `TESTING.md` and `QUICK_TEST.md`
- Review Allure TestOps API documentation
- Open an issue in the repository

