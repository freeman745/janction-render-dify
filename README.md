# JANCTION Render for Dify

Render Blender scenes and 3D models on cloud GPUs from Dify agents and workflows. Send a `.blend` file, a Blender
Python (bpy) script or a 3D file (GLB / glTF, FBX, USD, OBJ, STL, PLY, Alembic), get a preview in seconds with a
review of what is wrong and the bpy code to fix it, then render final frames or an MP4 on NVIDIA GPUs. No local GPU
or Blender is needed.

- Author: JasmyLab Inc. (operator of [JANCTION Render](https://render.janction.jp/?src=dify))
- Contact: contact@jasmylab.com
- Source: https://github.com/freeman745/janction-render-dify
- Type: tool plugin

## Setup

1. Install the plugin from the Dify Marketplace.
2. In Dify, open **Tools → JANCTION Render → Authorize** and save. The API key field is optional:
   - **Leave it empty** (recommended to start): on first use the plugin gets a free key for this workspace (no
     sign-up, no card; it starts with free GPU time) and keeps it in the plugin's storage.
   - **Enter a key** (`jr_...`) to use one you already have, for example one with prepaid credit. To get one by hand:
     `curl -X POST https://render.janction.jp/v1/keys`.

The plugin needs outbound HTTPS access to `render.janction.jp`. Scene files you give a tool are read from Dify and
sent to the service (up to 100 MB per file; pass larger scenes as an https link in `scene_url`).

## Tools

| Tool | What it does | GPU time |
|---|---|---|
| Render preview | 1-4 frames in seconds, with a review (verdict, issues, bpy fixes) and the images | free up to 2 GPU-minutes a day |
| Estimate render | GPU time, wait and price of a final before starting it | none |
| Render final | Final frames or video (PNG, EXR, MP4, WebM, ProRes, GIF, WebP); `max_yen` caps the cost (0 = free time only) | yes |
| Render status | Status of a job; image / video links when done | none |
| Download results | The result images and videos as Dify files | none |
| Cancel render | Stop a queued or running job | none |
| Scene info | Cameras, frame range, resolution and missing files of a scene, without rendering | none |
| Recent jobs | This key's recent jobs and the scenes still kept | none |
| Search 3D assets | Free CC0 models, textures and HDRIs from Poly Haven to use in a scene script | none |
| Share render / Unshare render | Publish a finished render as a public page, or take it down | none |
| Credit and usage | Free time left, balance and how to top up | none |
| Service status | Whether the GPUs are online and the expected wait | none |

A scene is given as one of: `scene_file` (a file), `scene_id` (from an earlier job, to render it again without
sending it), `scene_url` (an https link) or `scene_script` (bpy code that builds the scene).

## Usage

In an **Agent** app, add the JANCTION Render tools and ask, for example:

- "Render a preview of this .blend file and tell me if the lighting is wrong."
- "Make a 360-degree turntable MP4 of this GLB model."
- "Write a bpy script for a coffee cup on a wooden table and render it."

The tool descriptions tell the model to preview first, estimate, and ask before a final render.

In a **Workflow**, a typical chain is: Render preview → (check the review) → Estimate render → Render final with
`wait_seconds` 0 → Render status in a loop until `status` is `done` → Download results. A tool call waits at most
200 seconds; longer renders keep running and are picked up with Render status.

## Pricing

Each new key starts with a 100 JPY welcome credit of GPU time, and 400 JPY more after saving a card that is not
charged. Previews are free up to 2 GPU-minutes a day; after the free time, renders cost 0.1 JPY per GPU-second from
prepaid credit. A final never costs more than `max_yen`, and with the default 0 it only runs when it fits the free
time. Current prices: https://render.janction.jp/pricing

## Privacy

See [PRIVACY.md](PRIVACY.md). Scenes and results are deleted by the service 24 hours after last use. Topping up and
saving a card happen in the browser on links the tools return (Credit and usage, or a render refused for lack of
credit); the plugin never handles payment data.

## Links

- Website: https://render.janction.jp/?src=dify (Chinese: https://render.janction.jp/zh?src=dify)
- API reference: https://render.janction.jp/openapi.json
- Other ways to connect (MCP server, CLI, Python): https://github.com/JasmyLab-JANCTION/janction-render
