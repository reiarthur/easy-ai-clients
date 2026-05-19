# video.image_to_video(api="together")

Uses Together AI's `/v1/videos` workflow with an `image_url` payload for
image-to-video generation. Local image inputs are converted to data URLs by the
shared video media helper.

Environment variable: `TOGETHER_API_KEY`

Default model: `Wan-AI/Wan2.2-I2V-A14B`

Cost: `cost_source="unavailable"` unless Together returns stable usage/cost
metadata.

