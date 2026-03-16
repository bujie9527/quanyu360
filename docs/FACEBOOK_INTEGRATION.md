# Facebook / Meta Graph API Integration

## Functions

| Action | Description |
|--------|-------------|
| `create_post` | Create a Facebook Page post (message and/or link) |
| `comment_post` | Comment on an existing post |
| `send_message` | Send a Messenger message (requires recipient PSID) |

Uses Meta Graph API v25.0.

## Credentials

Store in `connector_config` or environment:

```json
{
  "connector_config": {
    "access_token": "your-page-access-token"
  }
}
```

Or set `FACEBOOK_ACCESS_TOKEN` in environment.

## Rate Limiting

The connector implements:

1. **X-App-Usage parsing** – Reads `call_count`, `total_time`, `total_cputime` from response headers
2. **Proactive throttling** – When any metric exceeds 75%, pauses before the next request
3. **429 retry** – On rate limit response, retries with exponential backoff (2^n seconds, up to 3 attempts)

## API Details

### create_post

- **Endpoint**: `POST /{page-id}/feed`
- **Required**: `page_id`; at least one of `message` or `link`
- **Permissions**: `pages_manage_posts`

### comment_post

- **Endpoint**: `POST /{object-id}/comments`
- **Required**: `post_id`, `message`
- **Permissions**: `pages_manage_engagement`

### send_message

- **Endpoint**: `POST /{page-id}/messages` (Messenger Send API)
- **Required**: `page_id`, `recipient_id` (PSID), `message`
- **Messaging type**: `RESPONSE` (default), `UPDATE`, or `MESSAGE_TAG`
- **Constraint**: Recipient must have messaged the Page within 24 hours, or have opted in for messages outside that window
- **Permissions**: `pages_messaging`
