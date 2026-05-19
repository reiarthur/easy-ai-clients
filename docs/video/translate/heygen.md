# HeyGen video.translate

Use HeyGen v3 video translation through `easy_ai_clients.video.translate(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.translate(
    video="source.mp4",
    output_languages=["Spanish"],
    api="heygen",
    sync=False,
)
```

This operation calls `POST /v3/video-translations`. Helper functions cover
translation list/get/update/delete, captions, language listing, and proofread
workflows.

