#!/usr/bin/env python3
"""
Open launches from Allure TestOps MCP Server
"""

import os
import sys
import asyncio
import json
from allure_client import AllureClient, create_allure_client

# Environment variables
ALLURE_TESTOPS_URL = os.environ.get('ALLURE_TESTOPS_URL')
ALLURE_TOKEN = os.environ.get('ALLURE_TOKEN')
PROJECT_ID = os.environ.get('PROJECT_ID')

if not ALLURE_TOKEN or not ALLURE_TESTOPS_URL or not PROJECT_ID:
    print('Error: ALLURE_TOKEN, ALLURE_TESTOPS_URL, and PROJECT_ID environment variables are required', file=sys.stderr)
    sys.exit(1)

async def get_all_open_launches():
    """Get all open launches from Allure TestOps"""
    client = create_allure_client(ALLURE_TESTOPS_URL, ALLURE_TOKEN)
    
    all_open_launches = []
    page = 0
    page_size = 100  # Get more per page to reduce API calls
    total_pages = None
    
    print(f"Fetching open launches from project {PROJECT_ID}...", file=sys.stderr)
    
    while True:
        params = {
            'page': page,
            'size': page_size
        }
        
        try:
            result = await client.get_launches(PROJECT_ID, params)
            
            if total_pages is None:
                total_pages = result.get('totalPages', 0)
                print(f"Total pages: {total_pages}, Total launches: {result.get('totalElements', 0)}", file=sys.stderr)
            
            launches = result.get('content', [])
            
            # Filter open launches (closed = false or null)
            open_launches = [
                launch for launch in launches 
                if not launch.get('closed', False)
            ]
            
            all_open_launches.extend(open_launches)
            
            print(f"Page {page + 1}/{total_pages}: Found {len(open_launches)} open launches (total so far: {len(all_open_launches)})", file=sys.stderr)
            
            # Check if this is the last page
            if result.get('last', False) or len(launches) == 0:
                break
            
            page += 1
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}", file=sys.stderr)
            break
    
    return all_open_launches

async def main():
    """Main function"""
    try:
        open_launches = await get_all_open_launches()
        
        # Output as JSON
        output = {
            'total': len(open_launches),
            'launches': open_launches
        }
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

