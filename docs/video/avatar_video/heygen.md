# HeyGen video.avatar_video

Use HeyGen v3 avatar video creation through `easy_ai_clients.video.avatar_video(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.avatar_video(
    avatar="avatar-or-look-id",
    text="Welcome to the demo.",
    voice_id="voice-id",
    api="heygen",
    sync=False,
)
```

This operation calls `POST /v3/videos` with `type="avatar"` when `avatar` is
provided, or `type="image"` when an image is provided instead.

