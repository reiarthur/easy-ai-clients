# webhook helpers(api="heygen")

HeyGen v3 webhook helpers live in `easy_ai_clients.webhooks`. They manage
endpoint registration, event type discovery, event history, and endpoint secret
rotation.

Credential: `HEYGEN_KEY`.

## Public helpers

| Helper | Endpoint | Notes |
| --- | --- | --- |
| `webhooks.list_endpoints(api="heygen")` | `GET /v3/webhooks/endpoints` | Lists configured webhook endpoints. |
| `webhooks.create_endpoint(url, api="heygen", **kwargs)` | `POST /v3/webhooks/endpoints` | Registers a webhook URL. Provider-native kwargs are forwarded. |
| `webhooks.update_endpoint(endpoint_id, api="heygen", **kwargs)` | `PATCH /v3/webhooks/endpoints/{endpoint_id}` | Updates endpoint fields. |
| `webhooks.delete_endpoint(endpoint_id, api="heygen", confirm=True)` | `DELETE /v3/webhooks/endpoints/{endpoint_id}` | Requires `confirm=True`. |
| `webhooks.rotate_secret(endpoint_id, api="heygen")` | `POST /v3/webhooks/endpoints/{endpoint_id}/rotate-secret` | Rotates the signing secret. |
| `webhooks.list_event_types(api="heygen")` | `GET /v3/webhooks/event-types` | Lists event types supported by the account/API. |
| `webhooks.list_events(api="heygen", **filters)` | `GET /v3/webhooks/events` | Lists webhook event history with provider-native filters. |

## Example

```python
from easy_ai_clients import webhooks

types = webhooks.list_event_types(api="heygen")
print(types["data"])

endpoint = webhooks.create_endpoint(
    "https://example.com/heygen/webhook",
    api="heygen",
    event_types=["video.completed", "video.failed"],
)
endpoint_id = endpoint["data"]["id"]

webhooks.rotate_secret(endpoint_id, api="heygen")
events = webhooks.list_events(api="heygen", limit=20)

webhooks.delete_endpoint(endpoint_id, api="heygen", confirm=True)
```

Responses include `provider`, `data`, and `raw_response`. Destructive delete
calls are guarded by `confirm=True` so accidental cleanup calls fail safely.

