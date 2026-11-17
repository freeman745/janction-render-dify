from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class SceneInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        job = api.post("/v1/jobs", {**jr.scene_fields(api, p), "kind": "info"})
        job = api.wait(job["job_id"], 90)
        if job.get("status") != "done":
            yield from jr.job_messages(self, job, show_images=False)
            return
        yield self.create_text_message(
            f"Scene {job.get('scene_id')}: use this scene_id to render it without sending it again.")
        yield self.create_json_message({"scene_id": job.get("scene_id"), "info": job.get("info"),
                                        "warnings": job.get("warnings") or []})
