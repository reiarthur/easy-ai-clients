# HeyGen video.agent_video

Use HeyGen v3 Video Agent through `easy_ai_clients.video.agent_video(..., api="heygen")`.

Credential: `HEYGEN_KEY`.

```python
from easy_ai_clients import video

result = video.agent_video(
    "Make a concise onboarding video.",
    api="heygen",
    mode="generate",
    sync=False,
)
```

The adapter calls `POST /v3/video-agents`. Use resource helpers such as
`list_agent_sessions`, `get_agent_session`, `send_agent_message`,
`stop_agent_session`, `list_agent_styles`, `get_agent_resource`, and
`list_agent_videos` for follow-up workflows.

