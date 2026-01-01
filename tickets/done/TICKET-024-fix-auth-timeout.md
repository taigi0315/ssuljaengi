# Ticket: Fix Video Creation Authorization Timeout

## Description

The user is experiencing a `Timeout` and `invalid_grant` error when running the `gossiptoon run` command. This appears to be related to the Google GenAI API authentication or connectivity.

## Error Log

```
google.api_core.exceptions.RetryError: Timeout of 600.0s exceeded, last exception: 503 Getting metadata from plugin failed with error: ('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})
```

## Goals

- [ ] Identify the root cause of the `invalid_grant` error.
- [ ] Fix the authentication configuration or credential handling.
- [ ] Verify the pipeline runs successfully without successful timeout.

## Acceptance Criteria

- `gossiptoon run` completes successfully or fails with a meaningful error message if credentials are invalid (not a timeout).
- `invalid_grant` error is resolved.
