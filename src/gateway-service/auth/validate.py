import os
import requests

def token(request):
    if "Authorization" not in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]

    if not token:
        return None, ("missing credentials", 401)

    auth_url = os.environ.get("AUTH_SVC_ADDRESS")
    if not auth_url:
        return None, ("auth service URL not configured", 500)

    try:
        response = requests.post(
            f"{auth_url}/validate",
            headers={"Authorization": token},
        )
    except requests.exceptions.RequestException as e:
        return None, (f"Auth service error: {str(e)}", 500)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
