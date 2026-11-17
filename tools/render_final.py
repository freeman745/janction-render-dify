from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderFinalTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        body = {**jr.scene_fields(api, p), **jr.render_settings(p), "kind": "final",
                "max_yen": jr.integer(p, "max_yen") or 0}
        job = api.post("/v1/jobs", body)
        job = api.wait(job["job_id"], float(p.get("wait_seconds") or 0))
        yield from jr.job_messages(self, job)
