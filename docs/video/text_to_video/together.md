# video.text_to_video(api="together")

Uses Together AI's current `/v1/videos` workflow for text-to-video generation.
The call can run synchronously with polling or return the submitted request
metadata with `sync=False`.

Environment variable: `TOGETHER_API_KEY`

Default model: `Wan-AI/Wan2.2-T2V-A14B`

Cost: `cost_source="unavailable"` unless Together returns a stable request
cost. The wrapper preserves provider metadata in `raw_response`.

