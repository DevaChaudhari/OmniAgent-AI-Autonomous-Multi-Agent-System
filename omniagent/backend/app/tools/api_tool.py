import requests

def fetch_data(url):
    try:
        response = requests.get(url)
        return response.text[:500]   # limit output
    except Exception as e:
        return str(e)