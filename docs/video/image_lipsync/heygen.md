# HeyGen video.image_lipsync

Use HeyGen v3 photo/image talking video creation through
`easy_ai_clients.video.image_lipsync(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.image_lipsync(
    image="portrait.png",
    audio="voice.mp3",
    api="heygen",
    sync=False,
)
```

This operation is backed by `POST /v3/videos` with `type="image"`. Local audio is
uploaded to HeyGen assets and referenced by `audio_asset_id`.

