"""
Allure TestOps REST API Client
Provides HTTP methods for interacting with Allure TestOps API
"""

import json
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin
import httpx


class AllureClient:
    """HTTP client for Allure TestOps API"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        return {
            'Authorization': f'Api-Token {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _build_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL with query parameters"""
        url = urljoin(self.base_url, path)
        if params:
            # Filter out None values and handle arrays
            filtered_params = {}
            for key, value in params.items():
                if value is not None:
                    if isinstance(value, list):
                        # For arrays, we need to append each value
                        filtered_params[key] = value
                    else:
                        filtered_params[key] = value
            
            # Build query string manually to handle arrays
            query_parts = []
            for key, value in filtered_params.items():
                if isinstance(value, list):
                    for item in value:
                        query_parts.append(f"{key}={item}")
                else:
                    query_parts.append(f"{key}={value}")
            
            if query_parts:
                url += '?' + '&'.join(query_parts)
        
        return url
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Perform GET request"""
        url = self._build_url(path, params)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
    
    async def post(self, path: str, body: Optional[Any] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        """Perform POST request"""
        url = self._build_url(path, params)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=body if body else None
            )
            response.raise_for_status()
            return response.json()
    
    async def patch(self, path: str, body: Any, params: Optional[Dict[str, Any]] = None) -> Any:
        """Perform PATCH request"""
        url = self._build_url(path, params)
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json=body
            )
            response.raise_for_status()
            return response.json()
    
    async def put(self, path: str, body: Any, params: Optional[Dict[str, Any]] = None) -> Any:
        """Perform PUT request"""
        url = self._build_url(path, params)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=self._get_headers(),
                json=body
            )
            response.raise_for_status()
            return response.json()
    
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Perform DELETE request"""
        url = self._build_url(path, params)
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self._get_headers())
            response.raise_for_status()
    
    # Test Case CRUD
    async def get_test_cases(self, project_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Get all test cases for a project"""
        query_params = {"projectId": project_id}
        if params:
            query_params.update(params)
        return await self.get("/api/rs/testcase", query_params)
    
    async def get_test_case(self, test_case_id: int) -> Any:
        """Get a specific test case by ID with overview (extended information)"""
        return await self.get(f"/api/testcase/{test_case_id}/overview")
    
    async def get_test_case_scenario(self, test_case_id: int) -> Any:
        """Get scenario (steps) for a test case"""
        return await self.get(f"/api/testcase/{test_case_id}/step")
    
    async def create_test_case_step(
        self, 
        body: Dict[str, Any],
        after_id: Optional[int] = None,
        before_id: Optional[int] = None,
        with_expected_result: bool = False
    ) -> Any:
        """Create a test case step
        
        Args:
            body: Step body containing testCaseId and either bodyJson (for text) or attachmentId
            after_id: Insert step after this step ID (mutually exclusive with before_id)
            before_id: Insert step before this step ID (mutually exclusive with after_id)
            with_expected_result: Include expected result section
        
        Returns:
            Created step object
        """
        params = {}
        if after_id is not None:
            params['afterId'] = after_id
        if before_id is not None:
            params['beforeId'] = before_id
        params['withExpectedResult'] = str(with_expected_result).lower()
        
        return await self.post("/api/testcase/step", body, params)
    
    async def create_test_case(self, project_id: str, test_case: Dict[str, Any]) -> Any:
        """Create a new test case"""
        body = {**test_case, "projectId": int(project_id)}
        return await self.post("/api/rs/testcase", body)
    
    async def update_test_case(self, test_case_id: int, test_case: Dict[str, Any]) -> Any:
        """Update an existing test case"""
        return await self.patch(f"/api/rs/testcase/{test_case_id}", test_case)
    
    async def delete_test_case(self, test_case_id: int) -> None:
        """Delete a test case"""
        await self.delete(f"/api/rs/testcase/{test_case_id}")
    
    async def get_test_case_custom_fields(self, test_case_id: int, project_id: str) -> Any:
        """Get custom field values for a test case with v2 format
        GET /api/testcase/:id/cfv?projectId=:project_id&v2=true
        Returns list of custom fields with their current values
        """
        return await self.get(f"/api/testcase/{test_case_id}/cfv", {"projectId": project_id, "v2": "true"})
    
    async def get_available_custom_fields(self, project_id: int) -> Any:
        """Get available custom fields for test cases in a project
        POST /api/testcase/cfv
        Body: { "projectId": int, "ids": [test_case_ids] }
        Returns list of available custom fields with their schemas
        """
        body = {
            "projectId": project_id
        }
        return await self.post("/api/testcase/cfv", body)
    
    async def update_test_case_custom_fields(self, test_case_id: int, custom_fields: List[Dict[str, Any]]) -> Any:
        """Update custom field values for a test case
        PATCH /api/testcase/{testCaseId}/cfv
        Body: array of CustomFieldWithValuesDto
        """
        return await self.post(f"/api/testcase/{test_case_id}/cfv", custom_fields)
    
    async def get_custom_field_values(self, project_id: int, custom_field_id: int, size: int = 100, page: int = 0) -> Any:
        """Get possible values for a custom field in a project
        GET /api/project/:project_id/cfv?customFieldId=:id&size=100&page=0
        Returns paginated list of available custom field values
        """
        params = {
            "customFieldId": custom_field_id,
            "size": size
        }
        if page > 0:
            params["page"] = page
        return await self.get(f"/api/project/{project_id}/cfv", params)
    
    async def bulk_create_test_cases(self, project_id: str, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk create test cases"""
        results = []
        for test_case in test_cases:
            try:
                result = await self.create_test_case(project_id, test_case)
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "testCase": test_case})
        return results
    
    # Launch CRUD
    async def get_launches(self, project_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Get all launches for a project"""
        query_params = {"projectId": project_id}
        if params:
            query_params.update(params)
        return await self.get("/api/rs/launch", query_params)
    
    async def get_launch(self, launch_id: int) -> Any:
        """Get a specific launch by ID"""
        return await self.get(f"/api/rs/launch/{launch_id}")
    
    async def create_launch(self, project_id: str, launch: Dict[str, Any]) -> Any:
        """Create a new launch"""
        body = {**launch, "projectId": int(project_id)}
        return await self.post("/api/rs/launch", body)
    
    async def update_launch(self, launch_id: int, launch: Dict[str, Any]) -> Any:
        """Update an existing launch"""
        return await self.patch(f"/api/rs/launch/{launch_id}", launch)
    
    async def delete_launch(self, launch_id: int) -> None:
        """Delete a launch"""
        await self.delete(f"/api/rs/launch/{launch_id}")
    
    async def close_launch(self, launch_id: int) -> Any:
        """Close a launch"""
        return await self.post(f"/api/rs/launch/{launch_id}/close")
    
    # Test Plan CRUD
    async def get_test_plans(self, project_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Get all test plans for a project"""
        query_params = {"projectId": project_id}
        if params:
            query_params.update(params)
        return await self.get("/api/rs/testplan", query_params)
    
    async def get_test_plan(self, test_plan_id: int) -> Any:
        """Get a specific test plan by ID"""
        return await self.get(f"/api/rs/testplan/{test_plan_id}")
    
    async def create_test_plan(self, project_id: str, test_plan: Dict[str, Any]) -> Any:
        """Create a new test plan"""
        body = {**test_plan, "projectId": int(project_id)}
        return await self.post("/api/rs/testplan", body)
    
    async def update_test_plan(self, test_plan_id: int, test_plan: Dict[str, Any]) -> Any:
        """Update an existing test plan"""
        return await self.patch(f"/api/rs/testplan/{test_plan_id}", test_plan)
    
    async def delete_test_plan(self, test_plan_id: int) -> None:
        """Delete a test plan"""
        await self.delete(f"/api/rs/testplan/{test_plan_id}")
    
    # Comments
    async def get_comments(self, test_case_id: int, page: Optional[int] = None, size: Optional[int] = None) -> Any:
        """Get comments for a test case
        GET /api/comment?testCaseId=:id&page=0&size=25
        page and size are optional, default size=10
        """
        params = {"testCaseId": test_case_id}
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size
        return await self.get("/api/comment", params)
    
    async def create_comment(self, test_case_id: int, body: str) -> Any:
        """Create a comment for a test case
        POST /api/comment
        Body: {"testCaseId": int, "body": str}
        """
        comment_body = {
            "testCaseId": test_case_id,
            "body": body
        }
        return await self.post("/api/comment", comment_body)


def create_allure_client(base_url: str, token: str) -> AllureClient:
    """Create and return AllureClient instance"""
    return AllureClient(base_url, token)

