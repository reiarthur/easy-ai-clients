# video.image_to_video(api="xai")

Uses xAI Imagine image-to-video through `POST /v1/videos/generations` with an
`image` object and polls `GET /v1/videos/{request_id}` when `sync=True`.

Environment variable: `XAI_API_KEY`

Default model: `grok-imagine-video`

Cost: estimated from xAI Imagine published per-second pricing. The wrapper uses
`$0.05/sec` for `480p` and `$0.07/sec` for `720p`.

