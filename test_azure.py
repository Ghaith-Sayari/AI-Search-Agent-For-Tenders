import os
import requests
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('OPENAI_API_KEY')

# Try to get deployment info from Azure
try:
    # This endpoint lists available API versions for the deployment
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Try to get models info
    url = f"{endpoint}/models?api-version=2024-12-01-preview"
    response = requests.get(url, headers=headers)
    print(f"Models endpoint status: {response.status_code}")
    print(f"Response: {response.text[:500]}\n")
    
    # Try alternate endpoint
    url2 = f"{endpoint.replace('/api/projects/', '/deployments/')}"
    print(f"Trying: {url2}\n")
    
except Exception as e:
    print(f"Error: {e}\n")

# Check what's in the endpoint URL structure
print(f"Endpoint: {endpoint}")
print(f"Endpoint parts: {endpoint.split('/')}")