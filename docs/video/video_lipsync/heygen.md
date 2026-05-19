# HeyGen video.video_lipsync

Use HeyGen v3 lipsync through `easy_ai_clients.video.video_lipsync(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.video_lipsync(
    video="source.mp4",
    audio="dub.mp3",
    api="heygen",
    sync=False,
)
```

This operation calls `POST /v3/lipsyncs`. Local video/audio files are uploaded to
HeyGen assets and sent as asset references; URLs and asset IDs are passed
through.

