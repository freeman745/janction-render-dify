from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderCancelTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        out = api.delete(f"/v1/jobs/{jr.text(p, 'job_id')}")
        yield self.create_text_message(f"Job {jr.text(p, 'job_id')} cancelled. Only GPU time already used is charged.")
        yield self.create_json_message(out)
