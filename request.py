import sys
import requests
import json  # Import JSON module

# Open the input file
f = open(sys.argv[1])

# Define the API URL
url = 'https://ssd.jpl.nasa.gov/api/horizons_file.api'

# Send the POST request
r = requests.post(url, data={'format': 'json'}, files={'input': f})

# Close the file
f.close()

# Check if the request was successful
if r.status_code == 200:
    try:
        # Parse the response as JSON
        data = r.json()
        # Save the JSON data to a new file
        with open("results.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
        print("Data successfully written to results.json")
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        print("Raw response text:", r.text)
else:
    print(f"Request failed with status code {r.status_code}")
    print("Response text:", r.text)
