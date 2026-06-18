import requests

try:
    response = requests.post("http://localhost:8000/api/reports/4/export", json={"format": "pdf"})
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
