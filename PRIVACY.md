# Privacy policy: JANCTION Render plugin for Dify

This plugin is published by JasmyLab Inc., the operator of JANCTION Render (https://render.janction.jp).

## What the plugin sends

When a tool runs, the plugin sends to `https://render.janction.jp` only what that tool needs:

- the JANCTION Render API key (as the `X-API-Key` header): the one you entered, or the free key the plugin
  created for your workspace;
- the scene you give the tool: the uploaded file, the bpy script text, the https link, or a scene_id;
- the render settings of the call (frames, resolution, preset, and so on), and for sharing, the title and note
  you give.

The plugin does not send your Dify conversations, other files, user names or any other data.

## What the plugin stores

When no API key is entered, the plugin creates a free key for your Dify workspace on first use (a request to
`https://render.janction.jp/v1/keys` with no personal data) and keeps only that key in Dify's plugin storage, so the
workspace keeps the same free time and credit. It stores nothing else: no logs, cache or copies of scenes or
results. Entering your own key in the plugin settings makes the plugin use that key instead.

## What the service keeps

JANCTION Render handles this data under its own privacy policy, https://render.janction.jp/privacy . In short:

- scenes, scripts and rendered results: kept to perform the render and return the results, and deleted 24 hours
  after last use (normally 7 days for keys that have paid 500 JPY or more in total, 30 days with an active monthly
  plan);
- the API key: stored as a hash while the key is in use;
- the IP address of requests: 90 days, for free-tier limits and abuse prevention;
- job metadata (file sizes, frame counts, resolution, GPU seconds, timestamps, failure reasons, client type):
  1 year, for billing, incident handling and improving the service;
- pages made with "Share render": public until you take them down with "Unshare render".

The contents of scenes and renders are never used for machine learning or for any purpose other than the service.

## Third parties

Traffic to the service passes through Cloudflare. Rendering runs on JANCTION's own GPUs; at busy times it may run
on GPUs rented from providers under contract, in an isolated environment per job that is deleted afterwards.
Payments, if you choose to top up, are handled by Stripe on its own page; the plugin never sees card data. The
service's privacy policy lists every provider.

## Contact

contact@jasmylab.com
