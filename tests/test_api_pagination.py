
import requests

API_URL = "https://jsonplaceholder.typicode.com/posts"

# Request first page with 10 records
response = requests.get(
    API_URL,
    params={
        "_page": 1,
        "_limit": 10
    },
    timeout=30
)

# Check API response
response.raise_for_status()

# Convert response to JSON
data = response.json()

# Display results
print("API pagination test completed!")
print("Records received:", len(data))

print("\nRecord IDs:")

for record in data:
    print(record["id"])
