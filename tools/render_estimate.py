from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderEstimateTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        body = {**jr.scene_fields(api, p), **jr.render_settings(p), "kind": "final"}
        est = api.post("/v1/estimate", body)
        cost = est.get("cost") or {}
        free = "fits in the free GPU time" if cost.get("free") else f"about {cost.get('estimated_yen')} JPY"
        yield self.create_text_message(
            f"Estimate: {est.get('human')} ({est.get('seconds')} GPU seconds, {est.get('frames')} frames), {free}. "
            "Tell the user and ask before render_final.")
        yield self.create_json_message(est)
