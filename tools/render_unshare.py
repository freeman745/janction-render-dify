from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderUnshareTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        out = api.delete(f"/v1/jobs/{jr.text(p, 'job_id')}/share")
        yield self.create_text_message("The shared page was taken down.")
        yield self.create_json_message(out)
