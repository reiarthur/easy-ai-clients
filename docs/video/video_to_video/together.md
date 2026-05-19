# video.video_to_video(api="together")

Uses Together AI's `/v1/videos` workflow with a `video_url` payload for
source-video guided generation or editing.

Environment variable: `TOGETHER_API_KEY`

Default model: `Wan-AI/Wan2.2-V2V-A14B`

Cost: `cost_source="unavailable"` unless Together returns stable usage/cost
metadata.

