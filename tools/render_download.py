from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import jr_api as jr


class RenderDownloadTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from jr.invoke(self, self.run, tool_parameters)

    def run(self, api: jr.JanctionApi, p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        job = api.get(f"/v1/jobs/{jr.text(p, 'job_id')}")
        if job.get("status") != "done":
            yield from jr.job_messages(self, job, show_images=False)
            return
        only = jr.text(p, "only").lower()
        links = []
        sent = 0
        for a in job.get("artifacts") or []:
            name = a.get("name", "")
            wanted = only in name.lower() if only else jr.is_media(name)
            if not wanted:
                continue
            if (a.get("size") or 0) <= jr.MAX_BLOB:
                yield self.create_blob_message(api.download(a["url"]),
                                               meta={"filename": name, "mime_type": jr.mime_of(name)})
                sent += 1
            else:
                links.append(f"{name}: {a.get('view_url') or a.get('url')}")
        msg = f"{sent} file(s) from job {job.get('job_id')}."
        if links:
            msg += " Too large to attach, download from the links (about 24 hours):\n" + "\n".join(links)
        if not sent and not links:
            names = ", ".join(a.get("name", "") for a in job.get("artifacts") or [])
            msg = "No files matched. Files of this job: " + names
        yield self.create_text_message(msg)
