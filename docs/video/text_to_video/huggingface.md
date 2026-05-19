# video.text_to_video(api="huggingface")

Uses Hugging Face Inference Providers for text-to-video models through the
stable inference endpoint. The wrapper accepts provider-native kwargs in the
request `parameters` object and returns the standard video result contract.

Environment variable: `HUGGINGFACE_API_KEY`

Default model: `Wan-AI/Wan2.1-T2V-1.3B`

Cost: `cost_source="unavailable"` unless Hugging Face returns
provider-independent usage/cost metadata.

