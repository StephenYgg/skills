#!/usr/bin/env python3
import argparse
import base64
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ENVIRONMENTS = {
    "bzy-pre": "https://pre-identity.bazhuayu.com",
    "bzy-prod": "https://identity.bazhuayu.com",
    "op-pre": "https://pre-identity.octoparse.com",
    "op-prod": "https://identity.octoparse.com",
}

CLIENT_ID = "Octopus"
USER_AGENT = "electron"
CLAIM_NAME_IDENTIFIER = (
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
)
CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
CLAIM_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"


class AccessError(Exception):
    pass


class TokenRequestError(AccessError):
    pass


class TokenRefreshError(AccessError):
    pass


def default_access_home():
    override = os.environ.get("OCTOPARSE_ACCESS_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".octoparse"


def access_file(access_home=None):
    return Path(access_home or default_access_home()) / "access.json"


def now_ms():
    return int(time.time() * 1000)


def load_store(access_home=None):
    path = access_file(access_home)
    if not path.exists():
        return {"users": []}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise AccessError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        raise AccessError(f"Invalid access store shape in {path}")
    return data


def save_store(store, access_home=None):
    path = access_file(access_home)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def token_url(env):
    if env not in ENVIRONMENTS:
        raise AccessError(f"Unknown env: {env}")
    return f"{ENVIRONMENTS[env]}/connect/token"


def http_post_form(url, data, headers):
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise TokenRequestError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise TokenRequestError(str(exc)) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise TokenRequestError(f"Token endpoint returned invalid JSON: {body}") from exc


def decode_jwt_payload(token):
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload.encode("ascii"))
        decoded = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def first_claim(claims, names):
    for name in names:
        value = claims.get(name)
        if value is not None:
            return str(value)
    return ""


def user_from_token(env, fallback_username, token_data, make_default, now_fn):
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    if not access_token or not refresh_token or expires_in is None:
        raise TokenRequestError("Token response missing access_token, refresh_token, or expires_in")

    claims = decode_jwt_payload(access_token)
    email = first_claim(claims, [CLAIM_EMAIL, "email"])
    return {
        "env": env,
        "userId": first_claim(
            claims, ["sub", CLAIM_NAME_IDENTIFIER, "nameid", "user_id", "userid", "uid"]
        ),
        "userName": first_claim(
            claims, [CLAIM_NAME, "preferred_username", "unique_name", "name", "userName", "username"]
        ),
        "email": email or fallback_username,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_token_expired": int(now_fn() + int(expires_in) * 1000),
        "env_default_account": bool(make_default),
    }


def account_matches(user, account):
    return account in {
        str(user.get("email", "")),
        str(user.get("userName", "")),
        str(user.get("userId", "")),
    }


def upsert_user(store, user):
    users = store["users"]
    if user.get("env_default_account"):
        for existing in users:
            if existing.get("env") == user["env"]:
                existing["env_default_account"] = False

    user_key = user.get("userId") or user.get("email")
    for index, existing in enumerate(users):
        same_env = existing.get("env") == user["env"]
        existing_key = existing.get("userId") or existing.get("email")
        same_identity = existing_key and existing_key == user_key
        same_email = user.get("email") and existing.get("email") == user.get("email")
        if same_env and (same_identity or same_email):
            users[index] = user
            return
    users.append(user)


def login(
    env,
    username,
    password,
    make_default=False,
    access_home=None,
    http_post=http_post_form,
    now_ms=now_ms,
):
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "client_id": CLIENT_ID,
    }
    headers = {"User-Agent": USER_AGENT}
    token_data = http_post(token_url(env), data, headers)
    user = user_from_token(env, username, token_data, make_default, now_ms)
    store = load_store(access_home)
    upsert_user(store, user)
    save_store(store, access_home)
    return user


def users_for_env(env, access_home=None):
    return [user for user in load_store(access_home)["users"] if user.get("env") == env]


def select_user(env, account=None, access_home=None, interactive=False):
    users = users_for_env(env, access_home)
    if account:
        matches = [user for user in users if account_matches(user, account)]
        if not matches:
            raise AccessError(f"No stored account matched {account!r} in {env}")
        if len(matches) > 1:
            raise AccessError(f"Multiple stored accounts matched {account!r} in {env}")
        return matches[0]

    defaults = [user for user in users if user.get("env_default_account")]
    if len(defaults) == 1:
        return defaults[0]
    if len(defaults) > 1:
        raise AccessError(f"Multiple default accounts found for {env}")
    if not users:
        raise AccessError(f"No stored accounts for {env}. Run login first.")
    if not interactive:
        raise AccessError(f"No default account for {env}. Pass --account or run interactively.")
    return prompt_account(users)


def prompt_account(users):
    for index, user in enumerate(users, start=1):
        label = user_label(user)
        print(f"{index}. {label}")
    while True:
        choice = input("Select account: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(users):
            return users[int(choice) - 1]
        print("Invalid selection.")


def user_label(user):
    parts = [user.get("email") or user.get("userName") or user.get("userId") or "<unknown>"]
    if user.get("env_default_account"):
        parts.append("(default)")
    return " ".join(parts)


def token_is_valid(user, now_fn):
    expired_at = int(user.get("access_token_expired") or 0)
    return bool(user.get("access_token")) and expired_at > now_fn()


def refresh_user(user, access_home=None, http_post=http_post_form, now_ms=now_ms):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user.get("refresh_token", ""),
        "client_id": CLIENT_ID,
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        token_data = http_post(token_url(user["env"]), data, headers)
    except TokenRequestError as exc:
        raise TokenRefreshError(
            "Refresh failed. Ask the user to provide the password and run login again."
        ) from exc

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    if not access_token or not refresh_token or expires_in is None:
        raise TokenRefreshError("Refresh response missing access_token, refresh_token, or expires_in")

    store = load_store(access_home)
    for existing in store["users"]:
        if existing.get("env") == user.get("env") and (
            existing.get("userId") == user.get("userId")
            or existing.get("email") == user.get("email")
        ):
            existing["access_token"] = access_token
            existing["refresh_token"] = refresh_token
            existing["access_token_expired"] = int(now_ms() + int(expires_in) * 1000)
            save_store(store, access_home)
            return access_token
    raise TokenRefreshError("Stored account disappeared before refresh could be saved")


def get_token(
    env,
    account=None,
    access_home=None,
    http_post=http_post_form,
    now_ms=now_ms,
    interactive=False,
):
    user = select_user(env, account=account, access_home=access_home, interactive=interactive)
    if token_is_valid(user, now_ms):
        return user["access_token"]
    return refresh_user(user, access_home=access_home, http_post=http_post, now_ms=now_ms)


def print_accounts(env, access_home=None):
    users = users_for_env(env, access_home)
    if not users:
        print(f"No stored accounts for {env}.")
        return
    for user in users:
        print(user_label(user))


def build_parser():
    parser = argparse.ArgumentParser(description="Manage Octoparse OAuth bearer tokens.")
    subparsers = parser.add_subparsers(dest="command")

    get_parser = subparsers.add_parser("get", help="Get a valid access token.")
    get_parser.add_argument("--env", choices=ENVIRONMENTS.keys())
    get_parser.add_argument("--account")

    login_parser = subparsers.add_parser("login", help="Log in and save tokens.")
    login_parser.add_argument("--env", choices=ENVIRONMENTS.keys())
    login_parser.add_argument("--username")
    login_parser.add_argument("--password")
    login_parser.add_argument("--default", action="store_true")

    list_parser = subparsers.add_parser("list", help="List stored accounts.")
    list_parser.add_argument("--env", choices=ENVIRONMENTS.keys())
    return parser


def prompt_env():
    envs = list(ENVIRONMENTS.keys())
    for index, env in enumerate(envs, start=1):
        print(f"{index}. {env} - {ENVIRONMENTS[env]}")
    while True:
        choice = input("Select environment: ").strip()
        if choice in ENVIRONMENTS:
            return choice
        if choice.isdigit() and 1 <= int(choice) <= len(envs):
            return envs[int(choice) - 1]
        print("Invalid environment.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    try:
        env = args.env or prompt_env()
        if args.command == "get":
            print(get_token(env, account=args.account, interactive=True))
        elif args.command == "login":
            username = args.username or input("Username: ").strip()
            password = args.password or getpass.getpass("Password: ")
            user = login(env, username, password, make_default=args.default)
            print(f"Saved token for {user_label(user)} in {env}.")
        elif args.command == "list":
            print_accounts(env)
        else:
            parser.error("unknown command")
    except AccessError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
