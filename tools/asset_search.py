from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class AssetSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        params = {"q": jr.text(p, "query")}
        if jr.text(p, "kind") and jr.text(p, "kind") != "all":
            params["kind"] = jr.text(p, "kind")
        out = api.get("/v1/assets/search", params=params)
        found = out.get("results") or []
        lines = [f"{r.get('spec')}: {r.get('name')} ({r.get('type')}, {r.get('license')})" for r in found[:10]]
        answer = ("Pass the spec in asset_urls:\n" + "\n".join(lines)) if lines else "Nothing found."
        yield self.create_text_message(answer)
        yield self.create_json_message(out)
