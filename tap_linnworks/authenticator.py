import requests
from singer_sdk.authenticators import APIKeyAuthenticator

class LinnworksAuthenticator(APIKeyAuthenticator):
    """Authenticator class for Linnworks."""

    @staticmethod
    def create_for_stream(stream, application_id, application_secret, installation_token):
        body = {
            "Token": installation_token,
            "ApplicationId": application_id,
            "ApplicationSecret": application_secret
        }
        response = requests.post(
            "https://api.linnworks.net/api/Auth/AuthorizeByApplication",
            json=body
        )
        response.raise_for_status()
        auth_token = response.json()["Token"]
        return LinnworksAuthenticator(
            stream=stream,
            key="Authorization",
            value=auth_token
        )