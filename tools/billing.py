from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class BillingTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield self.create_json_message(api.get("/v1/me"))
