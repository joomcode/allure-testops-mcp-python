"""
CSV Parser for Test Cases
Parses CSV content and converts it to test case objects
"""

import csv
from io import StringIO
from typing import List, Dict, Any


def parse_test_cases_from_csv(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV content and return list of test case dictionaries"""
    reader = csv.DictReader(StringIO(csv_content))
    test_cases = []
    
    for record in reader:
        # Skip empty lines
        if not record.get('name'):
            continue
        
        test_case = {
            'name': record.get('name', '').strip(),
            'description': record.get('description', '').strip() or '',
            'status': record.get('status', '').strip() or 'draft',
        }
        
        # Handle automated field - can be 'true', '1', 'True', etc.
        automated_str = record.get('automated', '').strip().lower()
        test_case['automated'] = automated_str in ('true', '1', 'yes')
        
        test_cases.append(test_case)
    
    return test_cases


