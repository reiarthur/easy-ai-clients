# Replicate Avatar Video API

## Overview

This adapter targets Replicate `prunaai/p-video-avatar` through
`easy_ai_clients.video.avatar_video(..., api="replicate")`.

Credential: `REPLICATE_API_TOKEN`.

## Model Coverage

| Model | Status | Pricing basis |
| --- | --- | --- |
| `prunaai/p-video-avatar`, alias `replicate_prunaai_p_video_avatar` | `implemented` | seconds by resolution; pass duration for cost. |

## Example

```python
from easy_ai_clients import video

result = video.avatar_video(
    image="portrait.png",
    audio="voice.mp3",
    api="replicate",
    model="replicate_prunaai_p_video_avatar",
    sync=False,
)
```

## Payload

The adapter submits a Replicate prediction to:

```text
POST /v1/models/prunaai/p-video-avatar/predictions
```

The request body uses:

- `input.image`;
- `input.audio`;
- `input.resolution`;
- `input.video_prompt`.

Local image and audio paths are encoded as data URLs by the shared video media
preprocessor.

## Async References

The adapter preserves safe Replicate prediction URLs when returned by the API.

Pass `task_url` back to `video.get_status(...)` or `video.get_result(...)` when
present. Calls with only `request_id`, `model`, and `api` reconstruct the
prediction URL.

## Pricing

Replicate public model pricing is estimated per second by resolution:

- `720p`: `$0.025` per second;
- `1080p`: `$0.045` per second.

When duration is not supplied, the adapter returns
`cost_source="unavailable"` instead of guessing.

No live Replicate call is made by the default test suite.
