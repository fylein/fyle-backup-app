import json
import requests

from fyle_backup_app import settings


class FyleOAuth2():
    """
    Utility class for Fyle Auth
    """

    def __init__(self):
        """
        initialize from settings
        """
        self.client_id = settings.FYLE_CLIENT_ID
        self.client_secret = settings.FYLE_CLIENT_SECRET
        self.authorize_uri = settings.FYLE_AUTHORIZE_URI
        self.redirect_uri = settings.FYLE_CALLBACK_URI
        self.token_url = settings.FYLE_TOKEN_URI

    def authorize(self, state):
        """
        Initiates the Fyle OAuth2.0 Authorize flow
        :param state:
        :return:
        """
        authorize_url = self.authorize_uri + '?response_type=code&client_id=' \
            + self.client_id + '&redirect_uri=' + self.redirect_uri \
            + '&scope=read' + '&state=' + state
        return authorize_url

    def get_refresh_token(self, authorization_code):
        """
        Exchange the authorisation_code for refresh token
        :param authorization_code:
        :return refresh token string
        """
        json_response = requests.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": authorization_code})
        data = json.loads(json_response.text)
        refresh_token = data.get("refresh_token")
        return refresh_token
