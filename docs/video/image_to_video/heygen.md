# HeyGen video.image_to_video

Use HeyGen v3 image video creation through `easy_ai_clients.video.image_to_video(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.image_to_video(
    "Hello from this photo.",
    image="portrait.png",
    api="heygen",
    voice_id="your-voice-id",
    sync=False,
)
```

This operation calls `POST /v3/videos` with `type="image"`. Local images are
encoded as HeyGen base64 asset inputs; URLs and asset IDs are passed through.

