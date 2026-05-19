# account helpers(api="heygen")

HeyGen account helpers live in `easy_ai_clients.account`. The current public
helper fetches the authenticated user/account payload and can be used before
live tests or paid workflows to inspect account-level metadata returned by
HeyGen.

Credential: `HEYGEN_KEY`.

## Public helper

| Helper | Endpoint | Notes |
| --- | --- | --- |
| `account.get_current_user(api="heygen")` | `GET /v3/users/me` | Returns the authenticated user's account payload. |

## Example

```python
from easy_ai_clients import account

me = account.get_current_user(api="heygen")
print(me["provider"])
print(me["data"])
```

Responses include `provider`, `data`, and `raw_response`. The adapter does not
interpret balance or plan fields because HeyGen may change the returned account
shape independently of this package.

