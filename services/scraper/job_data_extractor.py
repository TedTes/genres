import json
import requests
from typing import Dict, List, Any, Optional

class JobDataExtractor:
    """Extract structured job data from HTML using an LLM API."""
    
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize the extractor with API credentials.
        
        Args:
            api_key: API key for the LLM service
            api_url: URL endpoint for the LLM API
        """
        self.api_key = api_key
        self.api_url = api_url
    
    def parse_jobs(self, html_content: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Extract structured job information from HTML using an LLM.
        
        Args:
            html_content: HTML string containing job listings
            company_name: Name of the company
            
        Returns:
            List of dictionaries containing structured job information
        """
        # Create the prompt for the LLM
        prompt = self._create_prompt(html_content, company_name)
        
        # Send to LLM and get response
        llm_response = self._send_to_llm(prompt)
        
        # Parse and return the response
        return self._process_llm_response(llm_response)
    
    def _create_prompt(self, html_content: str, company_name: str) -> str:
        """Create a prompt for the LLM to extract job information."""
        return f"""
Extract structured information from these HTML job listings for {company_name}.

For each job posting, extract:
1. Job title
2. Location if available
3. Job type (full-time, part-time, etc.) if available
4. Description (a brief summary)
5. Requirements or qualifications if available
6. Application URL if available

Format the output as a JSON array of job objects.

HTML content:
{html_content}
"""
    
    def _send_to_llm(self, prompt: str) -> str:
        """
        Send the prompt to an LLM API and get the response.
    
        """
     
      
        if not self.api_key or not self.api_url:
            # TODO: implement custom error handling
            return '{"message": "NO API KEY , OR API URL FOUND !"}'
        
        # TODO: implementation for a generic LLM API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "max_tokens": 1000
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        return response.json()["choices"][0]["text"]
    
    def _process_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Process the LLM response into structured data."""
        # Handle potential errors in LLM response JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract just the JSON part if there's extra text
            try:
                # Look for what appears to be JSON array in the response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
                else:
                    return [{"error": "Failed to parse LLM response", "raw_response": response}]
            except Exception:
                return [{"error": "Failed to parse LLM response", "raw_response": response}]