---
name: octoparse-access
description: Manage Octoparse OAuth2/OIDC bearer access tokens for bzy-pre, bzy-prod, op-pre, and op-prod. Use when the user asks for an Octoparse access_token, token, authorization data, bearer token, or wants to log in, refresh, list, or select stored Octoparse accounts.
---

# Octoparse Access

Use the bundled script for token management. Do not hand-edit `~/.octoparse/access.json` unless the script is unavailable.

## Environments

| env | identity_url |
| --- | --- |
| `bzy-pre` | `https://pre-identity.bazhuayu.com` |
| `bzy-prod` | `https://identity.bazhuayu.com` |
| `op-pre` | `https://pre-identity.octoparse.com` |
| `op-prod` | `https://identity.octoparse.com` |

Always ask the user for `env` if they did not provide one.

## Safety Rules

- Never store passwords. Passwords are only accepted for the current `login` command and are not written to disk.
- Never commit `~/.octoparse/access.json` or copy its contents into repository files.
- Never guess the environment. Ask the user when `env` is missing.
- Never print or summarize stored refresh tokens.
- Only show the full access token when the user explicitly asks for the token value. Otherwise, say that a valid token was obtained or refreshed.

## Workflow

1. If the user asks for a token and did not provide an environment, ask which environment to use.
2. Run `python skills/octoparse-access/scripts/octoparse_access.py list --env <env>` to show stored accounts for that environment when the user did not specify an account.
3. Run `get` with the chosen environment and optional account.
4. If the stored access token is still valid, return it.
5. If it is expired, the script refreshes it with `refresh_token`, immediately saves the new `access_token`, `refresh_token`, and `access_token_expired`, then returns the token.
6. If refresh fails, report the error and tell the user they can provide a password to log in again.

When choosing an account, prefer email because it is less ambiguous. `--account` can match `email`, `userName`, or `userId`; if a name can match multiple accounts, ask the user to choose by email.

## JWT Claims

Decode the access token payload only to extract user metadata; do not validate the signature in this script.

| access.json field | Primary claim | Fallback claims |
| --- | --- | --- |
| `userId` | `sub` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier`, `nameid`, `user_id`, `userid`, `uid` |
| `userName` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` | `preferred_username`, `unique_name`, `name`, `userName`, `username` |
| `email` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` | `email`; if absent, use the login username |

## Commands

Get the default account token for an environment:

```bash
python skills/octoparse-access/scripts/octoparse_access.py get --env bzy-pre
```

Get a specific account token:

```bash
python skills/octoparse-access/scripts/octoparse_access.py get --env bzy-pre --account user@example.com
```

Log in with username and password:

```bash
python skills/octoparse-access/scripts/octoparse_access.py login --env bzy-pre --username user@example.com --password "<password>"
```

Log in and make the account the default for the environment:

```bash
python skills/octoparse-access/scripts/octoparse_access.py login --env bzy-pre --username user@example.com --password "<password>" --default
```

List accounts for an environment:

```bash
python skills/octoparse-access/scripts/octoparse_access.py list --env bzy-pre
```

## Data File

Data is stored at `~/.octoparse/access.json`, unless `OCTOPARSE_ACCESS_HOME` is set for tests.

```json
{
  "users": [
    {
      "env": "bzy-pre",
      "userId": "xxxx",
      "userName": "",
      "email": "xxx@xxx.com",
      "access_token": "",
      "refresh_token": "",
      "access_token_expired": 1710000000000,
      "env_default_account": true
    }
  ]
}
```

`access_token_expired` is an absolute Unix timestamp in milliseconds. Each environment can have only one default account.
