import requests
from typing import Optional, Dict, Any

from applifting_sdk.auth import SyncTokenManager
from applifting_sdk.helpers import JSONSerializer, ErrorHandler
from applifting_sdk.exceptions import (
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
)

from applifting_sdk.config import settings


class SyncBaseClient:
    """
    Base sync HTTP client that handles auth and sends requests to the API.
    """

    def __init__(self, token_manager: SyncTokenManager):
        self._base_url: str = settings.base_url
        self._token_manager: SyncTokenManager = token_manager
        self._session: requests.Session = requests.Session()
        self.error_handler: ErrorHandler = ErrorHandler()
        self.json_serializer: JSONSerializer = JSONSerializer()

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Sends an authenticated HTTP request.
        """
        token: str = self._token_manager.get_access_token()
        auth_headers: dict = {"Bearer": token}
        if headers:
            auth_headers.update(headers)

        if json:
            json = self.json_serializer.to_jsonable(json)

        try:
            url = f"{self._base_url.rstrip('/')}/{endpoint.lstrip('/')}"

            response: requests.Response = self._session.request(
                method=method,
                url=url,
                headers=auth_headers,
                params=params,
                json=json,
            )
        except requests.ConnectTimeout as e:
            raise AppliftingSDKTimeoutError("Connection timed out") from e
        except requests.ReadTimeout as e:
            raise AppliftingSDKTimeoutError("Read timed out") from e
        except (requests.ConnectionError, requests.RequestException) as e:
            raise AppliftingSDKNetworkError(str(e)) from e

        if not response.ok:
            self.error_handler.raise_api_error(response)

        return response

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
