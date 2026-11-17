"""Shared code for the JANCTION Render tools: the HTTP API client, scene inputs and job results.

API reference: https://render.janction.jp/openapi.json (every call sends the key as X-API-Key).
"""
from __future__ import annotations

import re
import time
from collections.abc import Callable, Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

SERVER = "https://render.janction.jp"
CLIENT = "dify-plugin/0.1.0"
SCENE_SUFFIXES = (".blend", ".py", ".fbx", ".glb", ".gltf", ".obj", ".stl", ".ply", ".usd", ".usda", ".usdc",
                  ".usdz", ".abc", ".spz")
MAX_UPLOAD = 100 * 1024 * 1024        # one request through the CDN; larger scenes go by https link (scene_url)
MAX_WAIT = 200                        # seconds a tool call may wait for a job (Dify stops plugin calls at about 250 s)
MAX_BLOB = 50 * 1024 * 1024           # results larger than this are returned as links only
FINISHED = ("done", "failed", "cancelled", "canceled", "expired")


class ApiError(Exception):
    def __init__(self, status: int, body: dict[str, Any]):
        self.status = status
        self.body = body
        super().__init__(f"{status} {body.get('error', '')}: {body.get('detail', '')}".strip())


class JanctionApi:
    def __init__(self, key: str):
        self.s = requests.Session()
        self.s.headers.update({"X-API-Key": key.strip(), "X-Client": CLIENT, "User-Agent": CLIENT})

    def call(self, method: str, path: str, timeout: float = 60, **kw: Any) -> Any:
        r = self.s.request(method, SERVER + path, timeout=timeout, **kw)
        if r.status_code >= 400:
            try:
                body = r.json()
            except ValueError:
                body = {"error": f"http_{r.status_code}", "detail": r.text[:300]}
            raise ApiError(r.status_code, body if isinstance(body, dict) else {"detail": str(body)})
        return r.json() if r.content else {}

    def get(self, path: str, **kw: Any) -> Any:
        return self.call("GET", path, **kw)

    def post(self, path: str, body: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self.call("POST", path, json=body or {}, **kw)

    def delete(self, path: str, **kw: Any) -> Any:
        return self.call("DELETE", path, **kw)

    def upload(self, name: str, data: bytes) -> str:
        r = self.call("POST", "/v1/files", timeout=600,
                      files={"file": (name, data, "application/octet-stream")})
        return r["scene_id"]

    def download(self, url: str) -> bytes:
        # the key only goes to our own server
        r = self.s.get(url, timeout=300) if url.startswith(SERVER + "/") else requests.get(url, timeout=300)
        r.raise_for_status()
        return r.content

    def wait(self, job_id: str, seconds: float) -> dict[str, Any]:
        """Poll the job until it finishes or `seconds` pass; return its last state."""
        end = time.monotonic() + max(0.0, min(seconds, MAX_WAIT))
        job = self.get(f"/v1/jobs/{job_id}")
        while job.get("status") not in FINISHED and time.monotonic() < end:
            time.sleep(min(5.0, max(1.0, end - time.monotonic())))
            job = self.get(f"/v1/jobs/{job_id}")
        return job


# ---- parameters ------------------------------------------------------------------------------

def text(p: dict[str, Any], name: str) -> str:
    v = p.get(name)
    return v.strip() if isinstance(v, str) else ("" if v is None else str(v))


def integer(p: dict[str, Any], name: str) -> int | None:
    v = p.get(name)
    if v in (None, ""):
        return None
    return int(float(v))


def number_list(s: str) -> list[int]:
    """'1, 40, 80' -> [1, 40, 80]"""
    return [int(x) for x in re.split(r"[\s,;]+", s) if x]


def scene_fields(api: JanctionApi, p: dict[str, Any]) -> dict[str, Any]:
    """The scene to render: an uploaded file, an earlier scene_id, an https link or bpy code (in that order)."""
    body: dict[str, Any] = {}
    f = p.get("scene_file")
    if f:
        name = getattr(f, "filename", None) or "scene" + (getattr(f, "extension", None) or "")
        if not name.lower().endswith(SCENE_SUFFIXES):
            raise ValueError(f"{name}: send a .blend, a Blender Python script (.py) or a 3D file "
                             f"({', '.join(SCENE_SUFFIXES[2:])})")
        try:
            data = f.blob
        except Exception as e:  # noqa: BLE001
            raise ValueError(
                f"Dify could not hand {name} to the plugin ({e}). On a self-hosted Dify, set FILES_URL and "
                "INTERNAL_FILES_URL so plugins can read uploaded files, or pass the scene as scene_url.") from e
        if len(data) > MAX_UPLOAD:
            raise ValueError(f"{name} is {len(data) // (1024 * 1024)} MB; files up to 100 MB can be sent here. "
                             "For a larger scene, put it at an https link and pass it as scene_url.")
        body["scene_id"] = api.upload(name, data)
    elif text(p, "scene_id"):
        body["scene_id"] = text(p, "scene_id")
    elif text(p, "scene_url"):
        body["scene_url"] = text(p, "scene_url")
    elif text(p, "scene_script"):
        body["scene_script"] = p["scene_script"]
    else:
        raise ValueError("Give the scene: scene_file, scene_id, scene_url (https) or scene_script (bpy code).")
    assets = [a for a in re.split(r"[\s,]+", text(p, "asset_urls")) if a]
    if assets and "scene_id" not in body:
        body["asset_urls"] = assets
    return body


def render_settings(p: dict[str, Any]) -> dict[str, Any]:
    """Optional render settings shared by preview, estimate and final; empty values are left to the service."""
    body: dict[str, Any] = {}
    for name in ("preset", "environment", "engine", "camera", "output", "blender"):
        if text(p, name) and text(p, name) != "none":
            body[name] = text(p, name)
    for name in ("width", "height", "samples", "fps", "frame_start", "frame_end"):
        v = integer(p, name)
        if v is not None:
            body[name] = v
    for name in ("transparent", "orbit"):
        if p.get(name) is True:
            body[name] = True
    if text(p, "frames"):
        body["frames"] = number_list(text(p, "frames"))
    return body


# ---- results ---------------------------------------------------------------------------------

KEEP = ("job_id", "kind", "status", "stage", "scene_id", "frame_start", "frame_end", "frames", "eta", "cost",
        "critic", "info", "warnings", "error", "next_render", "credit_hint", "links_expire_at", "expires_at_iso")


def job_summary(job: dict[str, Any]) -> dict[str, Any]:
    out = {k: job[k] for k in KEEP if job.get(k) not in (None, [], {})}
    files = []
    for a in job.get("artifacts") or []:
        files.append({k: a[k] for k in ("name", "size", "frame", "view_url", "url") if a.get(k) is not None})
    if files:
        out["files"] = files
    return out


def job_text(job: dict[str, Any]) -> str:
    st = job.get("status")
    jid = job.get("job_id")
    if st == "done":
        lines = [f"Job {jid} ({job.get('kind')}) finished. " + str((job.get("eta") or {}).get("human") or "")]
        crit = job.get("critic") or {}
        if crit.get("verdict"):
            lines.append(f"Review: {crit.get('verdict')} (score {crit.get('score')}).")
            for i in crit.get("issues") or []:
                if i.get("severity") != "info":
                    lines.append(f"- {i.get('message')}" + (f" Fix: {i.get('fix')}" if i.get("fix") else ""))
        for a in job.get("artifacts") or []:
            if a.get("name", "").endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov", ".exr")):
                lines.append(f"{a['name']}: {a.get('view_url') or a.get('url')}")
        lines.append("Links work for about 24 hours.")
        return "\n".join(lines)
    if st == "failed":
        return f"Job {jid} failed: {job.get('error')}"
    if st in FINISHED:
        return f"Job {jid} is {st}; it will not run further."
    eta = (job.get("eta") or {}).get("human") or ""
    return (f"Job {jid} is {st} {eta}".strip() + ". Check it again with render_status(job_id) in 10-20 seconds.")


def is_media(name: str) -> bool:
    return name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov"))


MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
        ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".exr": "image/x-exr",
        ".zip": "application/zip", ".blend": "application/octet-stream", ".txt": "text/plain",
        ".json": "application/json"}


def mime_of(name: str) -> str:
    m = re.search(r"\.[A-Za-z0-9]+$", name)
    return MIME.get(m.group(0).lower() if m else "", "application/octet-stream")


STORED_KEY = "janction_render_api_key"


def new_key() -> str:
    """A free key for this Dify workspace (no sign-up; it starts with free GPU time)."""
    r = requests.post(SERVER + "/v1/keys", json={"label": "Dify plugin", "source": "dify-plugin"},
                      headers={"X-Client": CLIENT, "User-Agent": CLIENT}, timeout=30)
    if r.status_code >= 400:
        raise ApiError(r.status_code, r.json() if r.content else {})
    return r.json()["api_key"]


def stored_key(tool: Tool, renew: bool = False) -> str:
    """The key this plugin created for the workspace earlier, or a new one (kept in the plugin's storage)."""
    storage = tool.session.storage
    if not renew:
        try:
            if storage.exist(STORED_KEY):
                key = storage.get(STORED_KEY).decode()
                if key.startswith("jr_"):
                    return key
        except Exception:  # noqa: BLE001 - storage unavailable: fall through and make a key
            pass
    key = new_key()
    storage.set(STORED_KEY, key.encode())
    return key


def api_for(tool: Tool, renew: bool = False) -> tuple[JanctionApi, bool]:
    """The key the user entered wins; without one, the workspace's own free key. Returns (api, is_stored_key)."""
    entered = (tool.runtime.credentials or {}).get("api_key") or ""
    if entered.strip():
        return JanctionApi(entered), False
    return JanctionApi(stored_key(tool, renew)), True


def invoke(tool: Tool, run: Callable[..., Generator[ToolInvokeMessage, None, None]],
           p: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
    """Run one tool and turn API errors into an answer the model and the user can act on."""
    try:
        api, stored = api_for(tool)
        try:
            yield from run(api, p)
        except ApiError as e:
            if not (stored and e.status == 401):
                raise
            # the stored key was revoked or expired on the service: make a new one once and retry
            api, _ = api_for(tool, renew=True)
            yield from run(api, p)
    except ApiError as e:
        raise ToolError(error_text(e)) from None
    except (ValueError, requests.RequestException) as e:
        raise ToolError(f"JANCTION Render: {e}") from None


class ToolError(Exception):
    """Raised so Dify shows the failure: the workflow node fails and an agent gets the message."""


def error_text(e: ApiError) -> str:
    body = e.body
    msg = f"JANCTION Render answered {e.status} {body.get('error', '')}: {body.get('detail', '')}".strip()
    if body.get("checkout_url"):
        msg += (f" This needs {body.get('needed_yen')} JPY of credit (balance {body.get('balance_yen')} JPY): the "
                f"user can top up at {body['checkout_url']} (tell them the price first).")
    if body.get("error") == "key_limit":
        msg += (" The plugin could not get a free key automatically. Enter an API key in the plugin settings "
                "(Tools > JANCTION Render > Authorize); one key is enough for the whole workspace.")
    return msg


def job_messages(tool: Tool, job: dict[str, Any], show_images: bool = True) -> Generator[ToolInvokeMessage, None, None]:
    yield tool.create_text_message(job_text(job))
    yield tool.create_json_message(job_summary(job))
    # plain variables for workflows: {{#node.job_id#}}, {{#node.status#}} ...
    first = next((a for a in job.get("artifacts") or [] if is_media(a.get("name", ""))), {})
    for name, value in (("job_id", job.get("job_id")), ("status", job.get("status")), ("scene_id", job.get("scene_id")),
                        ("result_url", first.get("view_url") or first.get("url"))):
        yield tool.create_variable_message(name, value or "")
    if show_images and job.get("status") == "done":
        for a in job.get("artifacts") or []:
            if a.get("name", "").lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")) and a.get("view_url"):
                yield tool.create_image_message(a["view_url"])
