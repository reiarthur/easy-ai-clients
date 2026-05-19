# HeyGen video resource helpers

HeyGen video resource helpers live under `easy_ai_clients.video` and use
`api="heygen"`. They complement generation calls such as `video.agent_video`,
`video.avatar_video`, `video.translate`, and lip-sync operations.

Credential: `HEYGEN_KEY`.

## Resource groups

| Group | Helpers |
| --- | --- |
| Videos | `list_videos`, `get_video`, `delete_video` |
| Lip-syncs | `list_lipsyncs`, `get_lipsync`, `update_lipsync`, `delete_lipsync` |
| Translations | `list_translations`, `get_translation`, `update_translation`, `delete_translation`, `get_translation_caption`, `list_translation_languages` |
| Proofreads | `create_proofread`, `get_proofread`, `generate_proofread`, `get_proofread_srt`, `update_proofread_srt` |
| Avatars | `list_avatars`, `get_avatar`, `delete_avatar`, `create_avatar_consent` |
| Avatar looks | `list_avatar_looks`, `get_avatar_look`, `update_avatar_look`, `delete_avatar_look` |
| Brand kits | `list_brand_kits` |
| Video Agent | `list_agent_sessions`, `get_agent_session`, `send_agent_message`, `stop_agent_session`, `list_agent_styles`, `get_agent_resource`, `list_agent_videos` |

## Examples

```python
from easy_ai_clients import video

videos = video.list_videos(api="heygen", limit=10)
video_id = videos["data"]["videos"][0]["video_id"]

details = video.get_video(video_id, api="heygen")
print(details["data"])
```

```python
from easy_ai_clients import video

proofread = video.create_proofread(
    video="source.mp4",
    output_languages=["Portuguese"],
    title="Portuguese review",
    api="heygen",
)

srt = video.get_proofread_srt(proofread["data"]["id"], api="heygen")
video.update_proofread_srt(
    proofread["data"]["id"],
    srt="captions.srt",
    api="heygen",
)
```

```python
from easy_ai_clients import video

session = video.agent_video(
    "Create a short product explainer.",
    api="heygen",
    sync=False,
)

video.send_agent_message(
    session["request_id"],
    "Make the ending more concise.",
    api="heygen",
)
```

All resource helpers return `provider`, `data`, and `raw_response`. Delete
helpers require `confirm=True` and are intended for explicit cleanup, not
implicit test teardown.

