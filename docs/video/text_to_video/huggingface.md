# video.text_to_video(api="huggingface")

Uses Hugging Face Inference Providers for text-to-video models through the
stable inference endpoint. The wrapper accepts provider-native kwargs in the
request `parameters` object and returns the standard video result contract.

Environment variable: `HUGGINGFACE_API_KEY`

Default model: `Wan-AI/Wan2.1-T2V-1.3B`

Cost: `cost_source="unavailable"` unless Hugging Face returns
provider-independent usage/cost metadata.

The current Hugging Face wrapper is synchronous. `sync=False` is accepted for
signature compatibility with other video providers, but it does not create a
provider async job and there are no `get_status`, `get_result`, or
`download_generation` helpers for Hugging Face text-to-video.
