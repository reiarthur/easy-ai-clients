# video.video_with_audio(api="runway")

Uses Runway's video/audio generation surface to create or attach audio for a
source video. Local videos are uploaded with the existing Runway ephemeral
upload helper before the task is submitted.

Environment variable: `RUNWAYML_API_SECRET`

Default model: `eleven_multilingual_v2`

Cost: estimated from Runway credits when duration metadata is supplied; otherwise
the wrapper uses the documented minimum-style fallback in `cost_details`.

