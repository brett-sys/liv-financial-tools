import requests
import json

print("Python is running correctly.")

payload = {
    "website": "https://example.com",
    "document_id": "1234567890123",
    "items": [
        {"item_name": "Widget A", "qty": 2, "unit_price": 35},
        {"item_name": "Service B", "qty": 1, "unit_price": 120}
    ]
}

print("Payload loaded:")
print(json.dumps(payload, indent=2))
