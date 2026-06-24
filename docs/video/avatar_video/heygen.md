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

## Photo Avatar Target

`model="heygen_photo_avatar"` maps to native target `avatar_iv/photo_avatar`.

When this model is selected and `avatar` is omitted, one public call creates a
Photo Avatar from the supplied image and then creates the video with the supplied
audio or script:

```python
from easy_ai_clients import video

result = video.avatar_video(
    image="portrait.png",
    audio="voice.mp3",
    api="heygen",
    model="heygen_photo_avatar",
    sync=False,
)
```

The Photo Avatar flow uses:

- `POST /v3/avatars` with `type="photo"`;
- `POST /v3/videos` with `type="avatar"` and the created `avatar_id`.

No live HeyGen call is made by the default test suite.
