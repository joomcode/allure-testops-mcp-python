#!/usr/bin/env python3
"""
Allure TestOps MCP Server
Model Context Protocol server for Allure TestOps API
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent

from allure_client import create_allure_client
from csv_parser import parse_test_cases_from_csv

load_dotenv()

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

# Define MCP tools
all_tools: List[Tool] = [
    Tool(
        name='test_cases',
        description='Read or write test case data from Allure TestOps. Use method="get" to fetch a specific test case by ID (includes scenario/steps), method="list" to get all test cases in a project with pagination, method="create" to create new test case, method="update" to modify existing test case, or method="delete" to remove a test case.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['get', 'list', 'create', 'update', 'delete'],
                    'description': 'Operation to perform: "get" for single test case, "list" for all test cases, "create" to create new, "update" to modify, or "delete" to remove'
                },
                'id': {'type': 'number', 'description': 'Test case ID (required for method=get, method=update or method=delete)'},
                'project_id': {'type': 'string', 'description': 'Project ID (required for method=list or method=create)'},
                'page': {'type': 'number', 'description': 'Page number (optional, for method=list)'},
                'size': {'type': 'number', 'description': 'Page size (optional, for method=list)'},
                'name': {'type': 'string', 'description': 'Test case name (for method=create or method=update)'},
                'description': {'type': 'string', 'description': 'Test case description (for method=create or method=update)'},
                'status': {'type': 'string', 'description': 'Test case status (for method=create or method=update)'},
                'automated': {'type': 'boolean', 'description': 'Is automated (for method=create or method=update)'},
            },
            'required': ['method'],
        },
    ),
    
    Tool(
        name='test_case_steps',
        description='Create, update or delete test case steps. Use method="create" to add a new step, method="update" to modify an existing step, or method="delete" to remove a step.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['create', 'update', 'delete'],
                    'description': 'Operation to perform: "create" to add a step, "update" to modify a step, "delete" to remove a step'
                },
                'test_case_id': {'type': 'number', 'description': 'Test case ID (required for method=create)'},
                'step_id': {'type': 'number', 'description': 'Step ID (required for method=update and method=delete)'},
                'text': {'type': 'string', 'description': 'Step text content (required for method=create and method=update)'},
                'after_id': {'type': 'number', 'description': 'Insert step after this step ID (optional, mutually exclusive with before_id)'},
                'before_id': {'type': 'number', 'description': 'Insert step before this step ID (optional, mutually exclusive with after_id)'},
                'with_expected_result': {'type': 'boolean', 'description': 'Include expected result section (default: false)'},
            },
            'required': ['method'],
        },
    ),
    
    Tool(
        name='launches',
        description='Read or write launch data from Allure TestOps. Use method="get" to fetch a specific launch by ID, method="list" to get all launches in a project with pagination, method="create" to create new launch, method="update" to modify existing launch, method="delete" to remove a launch, or method="close" to close a launch.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['get', 'list', 'create', 'update', 'delete', 'close'],
                    'description': 'Operation to perform: "get" for single launch, "list" for all launches, "create" to create new, "update" to modify, "delete" to remove, or "close" to close'
                },
                'id': {'type': 'number', 'description': 'Launch ID (required for method=get, method=update, method=delete, or method=close)'},
                'project_id': {'type': 'string', 'description': 'Project ID (required for method=list or method=create)'},
                'page': {'type': 'number', 'description': 'Page number (optional, for method=list)'},
                'size': {'type': 'number', 'description': 'Page size (optional, for method=list)'},
                'name': {'type': 'string', 'description': 'Launch name (for method=create or method=update)'},
                'closed': {'type': 'boolean', 'description': 'Is closed (for method=create or method=update)'},
            },
            'required': ['method'],
        },
    ),
    
    Tool(
        name='test_plans',
        description='Read or write test plan data from Allure TestOps. Use method="get" to fetch a specific test plan by ID, method="list" to get all test plans in a project with pagination, method="create" to create new test plan, method="update" to modify existing test plan, or method="delete" to remove a test plan.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['get', 'list', 'create', 'update', 'delete'],
                    'description': 'Operation to perform: "get" for single test plan, "list" for all test plans, "create" to create new, "update" to modify, or "delete" to remove'
                },
                'id': {'type': 'number', 'description': 'Test plan ID (required for method=get, method=update or method=delete)'},
                'project_id': {'type': 'string', 'description': 'Project ID (required for method=list or method=create)'},
                'page': {'type': 'number', 'description': 'Page number (optional, for method=list)'},
                'size': {'type': 'number', 'description': 'Page size (optional, for method=list)'},
                'name': {'type': 'string', 'description': 'Test plan name (for method=create or method=update)'},
                'description': {'type': 'string', 'description': 'Test plan description (for method=create or method=update)'},
            },
            'required': ['method'],
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
        name='test_case_custom_fields',
        description='Get or modify custom field values for a test case. Use method="get" to retrieve available custom fields and their current values, or method="modify" to add/remove a custom field value.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['get', 'modify'],
                    'description': 'Operation to perform: "get" to retrieve values, "modify" to add/remove values'
                },
                'test_case_id': {'type': 'number', 'description': 'Test case ID'},
                'project_id': {'type': 'string', 'description': 'Project ID'},
                'custom_field_id': {'type': 'number', 'description': 'Custom field ID (required for method=modify)'},
                'custom_field_value_id': {'type': 'number', 'description': 'Custom field value ID to add (required for mode=add)'},
                'mode': {'type': 'string', 'enum': ['add', 'delete'], 'description': 'Modification mode: "add" to add value, "delete" to remove all values for the field (required for method=modify)'},
            },
            'required': ['method', 'test_case_id', 'project_id'],
        },
    ),
    
    Tool(
        name='get_custom_field_values',
        description='Get possible values for a custom field in a project. Useful for discovering available options before modifying custom fields.',
        inputSchema={
            'type': 'object',
            'properties': {
                'project_id': {'type': 'number', 'description': 'Project ID'},
                'custom_field_id': {'type': 'number', 'description': 'Custom field ID'},
                'size': {'type': 'number', 'description': 'Page size (optional, default 100)'},
                'page': {'type': 'number', 'description': 'Page number (optional, default 0)'},
            },
            'required': ['project_id', 'custom_field_id'],
        },
    ),
    
    Tool(
        name='test_case_comments',
        description='Get, create or delete comments for a test case. Use method="get" to retrieve comments, method="create" to add a new comment, or method="delete" to remove a comment.',
        inputSchema={
            'type': 'object',
            'properties': {
                'method': {
                    'type': 'string',
                    'enum': ['get', 'create', 'delete'],
                    'description': 'Operation to perform: "get" to retrieve comments, "create" to add a comment, "delete" to remove a comment'
                },
                'test_case_id': {'type': 'number', 'description': 'Test case ID (required for method=get and method=create)'},
                'comment_id': {'type': 'number', 'description': 'Comment ID (required for method=delete)'},
                'body': {'type': 'string', 'description': 'Comment text (required for method=create)'},
                'page': {'type': 'number', 'description': 'Page number (optional, for method=get)'},
                'size': {'type': 'number', 'description': 'Page size (optional, for method=get, default 10)'},
            },
            'required': ['method'],
        },
    ),
]

# Helper functions
def simplify_test_case_status(data: Any) -> Any:
    """
    Simplify test case status from object to string in the response.
    Transforms status object {id, name, color, ...} to just the name string.
    Works with both list responses (content array) and single test case responses.
    """
    if isinstance(data, dict):
        # Handle list response with content array
        if 'content' in data and isinstance(data['content'], list):
            for item in data['content']:
                if isinstance(item, dict) and 'status' in item:
                    status = item.get('status')
                    if isinstance(status, dict) and 'name' in status:
                        item['status'] = status['name']
        # Handle single test case response
        elif 'status' in data:
            status = data.get('status')
            if isinstance(status, dict) and 'name' in status:
                data['status'] = status['name']
    
    return data

async def modify_test_case_custom_field_value_impl(
    test_case_id: int,
    project_id: str,
    custom_field_id: int,
    custom_field_value_id: Optional[int],
    mode: str
) -> Any:
    """
    Add or remove a custom field value to/from a test case.
    
    Args:
        test_case_id: Test case ID
        project_id: Project ID
        custom_field_id: Custom field ID
        custom_field_value_id: Custom field value ID (required for add mode, ignored for delete mode)
        mode: 'add' or 'delete'
    
    Returns:
        Result from update_test_case_custom_fields API call
    """
    # Get current custom field values
    current_cfv = await allure_client.get_test_case_custom_fields(test_case_id, project_id)
    
    # Build the update payload from current values
    custom_fields = []
    
    if mode == 'add':
        field_found = False
        
        for cfv_item in current_cfv:
            field_id = cfv_item.get('customField', {}).get('id')
            values = cfv_item.get('values', [])
            
            if field_id == custom_field_id:
                field_found = True
                # Add existing values
                for value in values:
                    custom_fields.append({
                        "customField": {"id": field_id},
                        "id": value.get('id')
                    })
                # Add new value if not already present
                if not any(v.get('id') == custom_field_value_id for v in values):
                    custom_fields.append({
                        "customField": {"id": field_id},
                        "id": custom_field_value_id
                    })
            else:
                # Keep existing values for other fields
                for value in values:
                    custom_fields.append({
                        "customField": {"id": field_id},
                        "id": value.get('id')
                    })
        
        # If field was not found in current values, add it
        if not field_found:
            custom_fields.append({
                "customField": {"id": custom_field_id},
                "id": custom_field_value_id
            })
    
    elif mode == 'delete':
        for cfv_item in current_cfv:
            field_id = cfv_item.get('customField', {}).get('id')
            values = cfv_item.get('values', [])
            
            if field_id == custom_field_id:
                # Skip all values for this field (effectively removing it)
                pass
            else:
                # Keep existing values for other fields
                for value in values:
                    custom_fields.append({
                        "customField": {"id": field_id},
                        "id": value.get('id')
                    })
    
    return await allure_client.update_test_case_custom_fields(test_case_id, custom_fields)

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
        # Test Cases - Combined operations
        if name == 'test_cases':
            method = arguments.get('method')
            
            if method == 'list':
                params = arguments.copy()
                project_id = params.pop('project_id')
                params.pop('method')
                result = await allure_client.get_test_cases(project_id, params)
                result = simplify_test_case_status(result)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'get':
                test_case_id = arguments.get('id')
                result = await allure_client.get_test_case(test_case_id)
                result = simplify_test_case_status(result)
                
                # Also fetch scenario (steps) for the test case
                try:
                    scenario = await allure_client.get_test_case_scenario(test_case_id)
                    result['scenario'] = scenario
                except Exception as e:
                    # If scenario fetch fails, add error info but don't fail the whole request
                    result['scenario'] = {"error": str(e)}
                
                # Also fetch first page of comments for the test case
                try:
                    comments = await allure_client.get_comments(test_case_id, page=0)
                    result['comments'] = comments
                except Exception as e:
                    # If comments fetch fails, add error info but don't fail the whole request
                    result['comments'] = {"error": str(e)}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'create':
                project_id = arguments.get('project_id')
                test_case = {k: v for k, v in arguments.items() if k not in ['method', 'project_id']}
                result = await allure_client.create_test_case(project_id, test_case)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'update':
                test_case_id = arguments.get('id')
                update_data = {k: v for k, v in arguments.items() if k not in ['method', 'id']}
                result = await allure_client.update_test_case(test_case_id, update_data)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'delete':
                test_case_id = arguments.get('id')
                await allure_client.delete_test_case(test_case_id)
                return [TextContent(type="text", text=f"Test case {test_case_id} deleted successfully")]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for test_cases: {method}")]
        
        # Test Case Steps - Create, Update, Delete
        elif name == 'test_case_steps':
            method = arguments.get('method')
            after_id = arguments.get('after_id')
            before_id = arguments.get('before_id')
            with_expected_result = arguments.get('with_expected_result', False)
            
            # Validate mutually exclusive parameters
            if after_id is not None and before_id is not None:
                return [TextContent(type="text", text="Error: after_id and before_id are mutually exclusive. Provide only one or neither.")]
            
            if method == 'create':
                test_case_id = arguments.get('test_case_id')
                if not test_case_id:
                    return [TextContent(type="text", text="Error: 'test_case_id' parameter is required for method=create")]
                text = arguments.get('text')
                if not text:
                    return [TextContent(type="text", text="Error: 'text' parameter is required for method=create")]
                
                # Build body for the request
                body = {
                    "testCaseId": test_case_id,
                    "bodyJson": {
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": text
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                # Create the step
                result = await allure_client.create_test_case_step(
                    body=body,
                    after_id=after_id,
                    before_id=before_id,
                    with_expected_result=with_expected_result
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'update':
                step_id = arguments.get('step_id')
                if not step_id:
                    return [TextContent(type="text", text="Error: 'step_id' parameter is required for method=update")]
                text = arguments.get('text')
                if not text:
                    return [TextContent(type="text", text="Error: 'text' parameter is required for method=update")]
                
                # Build body for the request (without testCaseId)
                body = {
                    "bodyJson": {
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": text
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                # Update the step
                result = await allure_client.update_test_case_step(
                    step_id=step_id,
                    body=body,
                    after_id=after_id,
                    before_id=before_id,
                    with_expected_result=with_expected_result
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'delete':
                step_id = arguments.get('step_id')
                if not step_id:
                    return [TextContent(type="text", text="Error: 'step_id' parameter is required for method=delete")]
                await allure_client.delete_test_case_step(step_id)
                return [TextContent(type="text", text=f"Step {step_id} deleted successfully")]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for test_case_steps: {method}")]
        
        # Launches - Combined operations
        elif name == 'launches':
            method = arguments.get('method')
            
            if method == 'list':
                params = arguments.copy()
                project_id = params.pop('project_id')
                params.pop('method')
                result = await allure_client.get_launches(project_id, params)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'get':
                launch_id = arguments.get('id')
                result = await allure_client.get_launch(launch_id)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'create':
                project_id = arguments.get('project_id')
                launch = {k: v for k, v in arguments.items() if k not in ['method', 'project_id']}
                result = await allure_client.create_launch(project_id, launch)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'update':
                launch_id = arguments.get('id')
                update_data = {k: v for k, v in arguments.items() if k not in ['method', 'id']}
                result = await allure_client.update_launch(launch_id, update_data)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'delete':
                launch_id = arguments.get('id')
                await allure_client.delete_launch(launch_id)
                return [TextContent(type="text", text=f"Launch {launch_id} deleted successfully")]
            
            elif method == 'close':
                launch_id = arguments.get('id')
                result = await allure_client.close_launch(launch_id)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for launches: {method}")]
        
        # Test Plans - Combined operations
        elif name == 'test_plans':
            method = arguments.get('method')
            
            if method == 'list':
                params = arguments.copy()
                project_id = params.pop('project_id')
                params.pop('method')
                result = await allure_client.get_test_plans(project_id, params)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'get':
                test_plan_id = arguments.get('id')
                result = await allure_client.get_test_plan(test_plan_id)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'create':
                project_id = arguments.get('project_id')
                test_plan = {k: v for k, v in arguments.items() if k not in ['method', 'project_id']}
                result = await allure_client.create_test_plan(project_id, test_plan)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'update':
                test_plan_id = arguments.get('id')
                update_data = {k: v for k, v in arguments.items() if k not in ['method', 'id']}
                result = await allure_client.update_test_plan(test_plan_id, update_data)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'delete':
                test_plan_id = arguments.get('id')
                await allure_client.delete_test_plan(test_plan_id)
                return [TextContent(type="text", text=f"Test plan {test_plan_id} deleted successfully")]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for test_plans: {method}")]
        
        # Special operations - Bulk CSV import
        elif name == 'bulk_create_test_cases_from_csv':
            project_id = arguments.get('project_id')
            csv_content = arguments.get('csv_content')
            test_cases = parse_test_cases_from_csv(csv_content)
            results = await allure_client.bulk_create_test_cases(project_id, test_cases)
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
        
        # Special operations - Custom Fields
        elif name == 'test_case_custom_fields':
            method = arguments.get('method')
            
            if method == 'get':
                test_case_id = arguments.get('test_case_id')
                project_id = arguments.get('project_id')
                result = await allure_client.get_test_case_custom_fields(test_case_id, project_id)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'modify':
                result = await modify_test_case_custom_field_value_impl(
                    test_case_id=arguments.get('test_case_id'),
                    project_id=arguments.get('project_id'),
                    custom_field_id=arguments.get('custom_field_id'),
                    custom_field_value_id=arguments.get('custom_field_value_id'),
                    mode=arguments.get('mode')
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for test_case_custom_fields: {method}")]
        
        # Special operations - Get custom field values
        elif name == 'get_custom_field_values':
            project_id = arguments.get('project_id')
            custom_field_id = arguments.get('custom_field_id')
            size = arguments.get('size', 100)
            page = arguments.get('page', 0)
            result = await allure_client.get_custom_field_values(project_id, custom_field_id, size, page)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # Special operations - Comments
        elif name == 'test_case_comments':
            method = arguments.get('method')
            
            if method == 'get':
                test_case_id = arguments.get('test_case_id')
                if not test_case_id:
                    return [TextContent(type="text", text="Error: 'test_case_id' parameter is required for method=get")]
                page = arguments.get('page')
                size = arguments.get('size')
                result = await allure_client.get_comments(test_case_id, page, size)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'create':
                test_case_id = arguments.get('test_case_id')
                if not test_case_id:
                    return [TextContent(type="text", text="Error: 'test_case_id' parameter is required for method=create")]
                body = arguments.get('body')
                if not body:
                    return [TextContent(type="text", text="Error: 'body' parameter is required for creating a comment")]
                result = await allure_client.create_comment(test_case_id, body)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif method == 'delete':
                comment_id = arguments.get('comment_id')
                if not comment_id:
                    return [TextContent(type="text", text="Error: 'comment_id' parameter is required for method=delete")]
                await allure_client.delete_comment(comment_id)
                return [TextContent(type="text", text=f"Comment {comment_id} deleted successfully")]
            
            else:
                return [TextContent(type="text", text=f"Unknown method for test_case_comments: {method}")]
        
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
        is_json_response_enabled=True
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
