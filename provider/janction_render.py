from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.jr_api import ApiError, JanctionApi


class JanctionRenderProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        key = (credentials.get("api_key") or "").strip()
        if not key:
            return  # no key: the tools get a free key for this workspace on first use
        if not key.startswith("jr_"):
            raise ToolProviderCredentialValidationError(
                "A JANCTION Render API key starts with jr_. Leave the field empty to get a free key automatically."
            )
        try:
            JanctionApi(key).get("/v1/me")
        except ApiError as e:
            raise ToolProviderCredentialValidationError(f"JANCTION Render refused the key: {e}") from e
