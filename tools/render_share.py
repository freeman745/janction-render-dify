from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderShareTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        body = {"title": jr.text(p, "title"), "note": jr.text(p, "note"), "listed": p.get("listed") is True}
        out = api.post(f"/v1/jobs/{jr.text(p, 'job_id')}/share", body)
        yield self.create_text_message(f"Shared: {out.get('url') or out}")
        yield self.create_json_message(out)
