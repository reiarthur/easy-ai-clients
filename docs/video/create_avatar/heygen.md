# HeyGen video.create_avatar

Use HeyGen v3 avatar creation through `easy_ai_clients.video.create_avatar(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.create_avatar(
    image="portrait.png",
    name="Support Agent",
    api="heygen",
)
```

The adapter calls `POST /v3/avatars`. By default it creates a photo avatar from
`image`; pass `prompt=...` for prompt avatar creation or `video_path` /
`video_url` for digital-twin creation.

