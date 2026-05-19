# media helpers(api="heygen")

HeyGen v3 asset helpers live in `easy_ai_clients.media`. Use them when a
HeyGen video, voice, proofread, or lip-sync workflow needs a reusable provider
asset.

Credential: `HEYGEN_KEY`.

## Public helpers

| Helper | Endpoint | Notes |
| --- | --- | --- |
| `media.upload_asset(file, api="heygen")` | `POST /v3/assets` | Uploads a local file path to HeyGen. |
| `media.delete_asset(asset_id, api="heygen", confirm=True)` | `DELETE /v3/assets/{asset_id}` | Requires explicit `confirm=True` because it is destructive. |

## Example

```python
from easy_ai_clients import media, video

asset = media.upload_asset("intro.mp4", api="heygen")
asset_id = asset["data"]["asset_id"]

result = video.translate(
    video_asset_id=asset_id,
    output_languages=["Spanish"],
    api="heygen",
    sync=False,
)

media.delete_asset(asset_id, api="heygen", confirm=True)
```

Responses include `provider`, `data`, and `raw_response`. The helper does not
download or transform media locally beyond the upload request.

