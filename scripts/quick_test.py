import requests

if __name__ == "__main__":
    try:
        r = requests.get("http://localhost:8000/health", timeout=3)
        print(r.status_code, r.json())
    except Exception as e:
        print("Server not running:", e)
