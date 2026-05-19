# HeyGen video.text_to_video

Use HeyGen v3 Video Agent through `easy_ai_clients.video.text_to_video(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.text_to_video(
    "Create a short product launch video.",
    api="heygen",
    sync=False,
)
```

This operation calls `POST /v3/video-agents`. Provider-native fields such as
`style_id`, `voice_id`, `avatar_id`, `brand_kit_id`, `files`, `mode`, and
`orientation` may be passed as keyword arguments.

