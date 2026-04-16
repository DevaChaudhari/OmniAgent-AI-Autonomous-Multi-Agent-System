import requests

def fetch_data(url):
    try:
        response = requests.get(url)
        return response.text[:500] 
    except Exception as e:
        return str(e)
