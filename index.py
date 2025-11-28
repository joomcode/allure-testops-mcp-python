#!/usr/bin/env python3
"""
Allure TestOps MCP Server
Model Context Protocol server for Allure TestOps API
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent

from allure_client import AllureClient, create_allure_client
from csv_parser import parse_test_cases_from_csv

# Environment variables
ALLURE_TESTOPS_URL = os.environ.get('ALLURE_TESTOPS_URL')
ALLURE_TOKEN = os.environ.get('ALLURE_TOKEN')
MCP_TRANSPORT = os.environ.get('MCP_TRANSPORT', 'stdio')  # stdio or streamable_http
MCP_ADDRESS = os.environ.get('MCP_ADDRESS', '0.0.0.0:8000')  # host:port

# Validate required environment variables
if not ALLURE_TOKEN:
    print('Error: ALLURE_TOKEN environment variable is required', file=sys.stderr)
    sys.exit(1)

if not ALLURE_TESTOPS_URL:
    print('Error: ALLURE_TESTOPS_URL environment variable is required', file=sys.stderr)
    sys.exit(1)

# Initialize Allure client
allure_client = create_allure_client(ALLURE_TESTOPS_URL, ALLURE_TOKEN)

# Define tools matching Node.js version
all_tools: List[Tool] = [
    Tool(
        name='list_test_cases',
        description='List all test cases in the project',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'page': {'type': 'number', 'description': 'Page number (optional)'},
                'size': {'type': 'number', 'description': 'Page size (optional)'},
            },
            'required': ['project_id'],
        },
    ),
    Tool(
        name='get_test_case',
        description='Get a specific test case by ID',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test case ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='create_test_case',
        description='Create a new test case',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'name': {'type': 'string', 'description': 'Test case name'},
                'description': {'type': 'string', 'description': 'Test case description'},
                'status': {'type': 'string', 'description': 'Test case status'},
                'automated': {'type': 'boolean', 'description': 'Is automated'},
            },
            'required': ['project_id', 'name'],
        },
    ),
    Tool(
        name='update_test_case',
        description='Update an existing test case',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test case ID'},
                'name': {'type': 'string', 'description': 'Test case name'},
                'description': {'type': 'string', 'description': 'Test case description'},
                'status': {'type': 'string', 'description': 'Test case status'},
                'automated': {'type': 'boolean', 'description': 'Is automated'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='delete_test_case',
        description='Delete a test case',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test case ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='bulk_create_test_cases_from_csv',
        description='Bulk create test cases from CSV content. CSV should have columns: name, description, status, automated',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'csv_content': {'type': 'string', 'description': 'CSV file content'},
            },
            'required': ['project_id', 'csv_content'],
        },
    ),
    Tool(
        name='list_launches',
        description='List all launches in the project',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'page': {'type': 'number', 'description': 'Page number (optional)'},
                'size': {'type': 'number', 'description': 'Page size (optional)'},
            },
            'required': ['project_id'],
        },
    ),
    Tool(
        name='get_launch',
        description='Get a specific launch by ID',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Launch ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='create_launch',
        description='Create a new launch',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'name': {'type': 'string', 'description': 'Launch name'},
                'closed': {'type': 'boolean', 'description': 'Is closed'},
            },
            'required': ['project_id', 'name'],
        },
    ),
    Tool(
        name='update_launch',
        description='Update an existing launch',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Launch ID'},
                'name': {'type': 'string', 'description': 'Launch name'},
                'closed': {'type': 'boolean', 'description': 'Is closed'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='delete_launch',
        description='Delete a launch',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Launch ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='close_launch',
        description='Close a launch',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Launch ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='list_test_plans',
        description='List all test plans in the project',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'page': {'type': 'number', 'description': 'Page number (optional)'},
                'size': {'type': 'number', 'description': 'Page size (optional)'},
            },
            'required': ['project_id'],
        },
    ),
    Tool(
        name='get_test_plan',
        description='Get a specific test plan by ID',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test plan ID'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='create_test_plan',
        description='Create a new test plan',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'name': {'type': 'string', 'description': 'Test plan name'},
                'description': {'type': 'string', 'description': 'Test plan description'},
            },
            'required': ['project_id', 'name'],
        },
    ),
    Tool(
        name='update_test_plan',
        description='Update an existing test plan',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test plan ID'},
                'name': {'type': 'string', 'description': 'Test plan name'},
                'description': {'type': 'string', 'description': 'Test plan description'},
            },
            'required': ['id'],
        },
    ),
    Tool(
        name='delete_test_plan',
        description='Delete a test plan',
        inputSchema={
            'type': 'object',
            'properties': {
                'id': {'type': 'number', 'description': 'Test plan ID'},
            },
            'required': ['id'],
        },
    ),
]

# Create MCP server
server = Server("allure-testops-mcp")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Return list of available tools"""
    return all_tools

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == 'list_test_cases':
            params = arguments or {}
            project_id = params.pop('project_id')
            result = await allure_client.get_test_cases(project_id, params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'get_test_case':
            test_case_id = arguments.get('id')
            result = await allure_client.get_test_case(test_case_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'create_test_case':
            project_id = arguments.pop('project_id')
            test_case = {k: v for k, v in arguments.items()}
            result = await allure_client.create_test_case(project_id, test_case)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'update_test_case':
            test_case_id = arguments.get('id')
            update_data = {k: v for k, v in arguments.items() if k != 'id'}
            result = await allure_client.update_test_case(test_case_id, update_data)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'delete_test_case':
            test_case_id = arguments.get('id')
            await allure_client.delete_test_case(test_case_id)
            return [TextContent(type="text", text=f"Test case {test_case_id} deleted successfully")]

        elif name == 'bulk_create_test_cases_from_csv':
            project_id = arguments.get('project_id')
            csv_content = arguments.get('csv_content')
            test_cases = parse_test_cases_from_csv(csv_content)
            results = await allure_client.bulk_create_test_cases(project_id, test_cases)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == 'list_launches':
            params = arguments or {}
            project_id = params.pop('project_id')
            result = await allure_client.get_launches(project_id, params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'get_launch':
            launch_id = arguments.get('id')
            result = await allure_client.get_launch(launch_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'create_launch':
            project_id = arguments.pop('project_id')
            launch = {k: v for k, v in arguments.items()}
            result = await allure_client.create_launch(project_id, launch)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'update_launch':
            launch_id = arguments.get('id')
            update_data = {k: v for k, v in arguments.items() if k != 'id'}
            result = await allure_client.update_launch(launch_id, update_data)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'delete_launch':
            launch_id = arguments.get('id')
            await allure_client.delete_launch(launch_id)
            return [TextContent(type="text", text=f"Launch {launch_id} deleted successfully")]

        elif name == 'close_launch':
            launch_id = arguments.get('id')
            result = await allure_client.close_launch(launch_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'list_test_plans':
            params = arguments or {}
            project_id = params.pop('project_id')
            result = await allure_client.get_test_plans(project_id, params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'get_test_plan':
            test_plan_id = arguments.get('id')
            result = await allure_client.get_test_plan(test_plan_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'create_test_plan':
            project_id = arguments.pop('project_id')
            test_plan = {k: v for k, v in arguments.items()}
            result = await allure_client.create_test_plan(project_id, test_plan)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'update_test_plan':
            test_plan_id = arguments.get('id')
            update_data = {k: v for k, v in arguments.items() if k != 'id'}
            result = await allure_client.update_test_plan(test_plan_id, update_data)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == 'delete_test_plan':
            test_plan_id = arguments.get('id')
            await allure_client.delete_test_plan(test_plan_id)
            return [TextContent(type="text", text=f"Test plan {test_plan_id} deleted successfully")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as error:
        error_message = str(error)
        # Try to extract more details from httpx errors
        if hasattr(error, 'response') and hasattr(error.response, 'text'):
            error_message += f"\n{error.response.text}"
        return [TextContent(type="text", text=f"Error: {error_message}")]

async def main_stdio():
    """Main function to run the server in stdio mode"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

async def main_streamable_http(host: str, port: int):
    """Main function to run the server in Streamable HTTP mode
    
    Note: Streamable HTTP transport is complex and requires proper session management.
    For production use, consider using stdio transport or implementing full session lifecycle.
    """
    import uvicorn

    # Single global transport instance
    transport = StreamableHTTPServerTransport(
        mcp_session_id=None,
        is_json_response_enabled=False
    )

    # Track if server is initialized
    server_initialized = asyncio.Event()
    server_task = None

    async def init_mcp_server():
        """Initialize MCP server once at startup"""
        async with transport.connect() as (read_stream, write_stream):
            server_initialized.set()
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
                stateless=True
            )

    async def asgi_app(scope, receive, send):
        """ASGI application handler"""
        nonlocal server_task

        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    server_task = asyncio.create_task(init_mcp_server())
                    await server_initialized.wait()
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    if server_task:
                        server_task.cancel()
                        try:
                            await server_task
                        except asyncio.CancelledError:
                            pass
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        elif scope["type"] == "http":
            path = scope.get("path", "")

            if path == "/health/liveness":
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"status": "alive"}).encode("utf-8"),
                })
                return

            elif path == "/health/readiness":
                is_ready = server_initialized.is_set()

                status_code = 200 if is_ready else 503
                await send({
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({
                        "status": "ready" if is_ready else "not_ready",
                        "server_initialized": server_initialized.is_set(),
                    }).encode("utf-8"),
                })
                return

            if not server_initialized.is_set():
                await server_initialized.wait()

            await transport.handle_request(scope, receive, send)

    config = uvicorn.Config(
        app=asgi_app,
        host=host,
        port=port,
        log_level="info",
        lifespan="on"
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    print(f"Allure TestOps MCP Server", file=sys.stderr)
    print(f"Transport: {MCP_TRANSPORT}", file=sys.stderr)
    print(f"Connected to: {ALLURE_TESTOPS_URL}", file=sys.stderr)
    print(f"Registered {len(all_tools)} tools", file=sys.stderr)

    if MCP_TRANSPORT == 'stdio':
        print("Running on stdio", file=sys.stderr)
        asyncio.run(main_stdio())
    elif MCP_TRANSPORT == 'streamable_http':
        # Parse host:port from MCP_ADDRESS
        if ':' in MCP_ADDRESS:
            host, port_str = MCP_ADDRESS.rsplit(':', 1)
            port = int(port_str)
        else:
            host = MCP_ADDRESS
            port = 8000
        print(f"Running on streamable_http at http://{host}:{port}", file=sys.stderr)
        asyncio.run(main_streamable_http(host, port))
    else:
        print(f"Error: Unknown transport mode: {MCP_TRANSPORT}", file=sys.stderr)
        print("Supported modes: stdio, streamable_http", file=sys.stderr)
        print("Set MCP_TRANSPORT environment variable to 'stdio' or 'streamable_http'", file=sys.stderr)
        sys.exit(1)
