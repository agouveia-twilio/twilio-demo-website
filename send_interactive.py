#!/usr/bin/env python3
"""
Send an interactive Webchat message (buttons / dropdown / calendar) into a Flex conversation.

This is the *sending* half of the interactive elements rendered by index.html. It posts a
message to the Conversations API with an `interactiveWebchatOptions` block in the message
Attributes -- exactly what a Studio "Send & Wait For Reply" widget would put there, but
without needing a Flow, so you can test the widget end to end.

Credentials (env):
    TWILIO_ACCOUNT_SID      ACxxxx
    TWILIO_AUTH_TOKEN       your auth token
    TWILIO_CHAT_SERVICE_SID ISxxxx   (optional; the Flex Conversation Service.
                                      Required if the conversation is not in the
                                      account's *default* Conversations service --
                                      which is the case for Flex.)

Usage:
    # 1. Find the conversation to target (start a chat on the site first)
    python3 send_interactive.py --list

    # 2. Send each element type
    python3 send_interactive.py --conversation CHxxx --type buttons \
        --body "How can I help?" \
        --option "Track my order=track-order" \
        --option "Return an item=return-item"

    python3 send_interactive.py --conversation CHxxx --type dropdown \
        --body "Pick a product line" --label "Seasonal boxes..." \
        --option "Spring box=spring-box" --option "Summer box=summer-box"

    python3 send_interactive.py --conversation CHxxx --type calendar \
        --body "When should we deliver?" --timezone Europe/Dublin
"""

import argparse
import base64
import json
import os
import sys
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://conversations.twilio.com/v1"

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
CHAT_SERVICE_SID = os.environ.get("TWILIO_CHAT_SERVICE_SID", "")


def api(path: str, data: dict | None = None) -> dict:
    """GET (data=None) or POST form-encoded to the Conversations API with Basic Auth."""
    token = base64.b64encode(f"{ACCOUNT_SID}:{AUTH_TOKEN}".encode()).decode()
    headers = {"Authorization": f"Basic {token}"}
    body = None
    if data is not None:
        body = urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(f"{API_BASE}{path}", data=body, headers=headers)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


def scope(conversation_sid: str) -> str:
    """
    Flex conversations live in the Flex Conversation Service, not the account's default
    service, so they must be addressed under /Services/{IS...}/. Without the service SID
    the unscoped path only resolves conversations in the default service.
    """
    if CHAT_SERVICE_SID:
        return f"/Services/{CHAT_SERVICE_SID}/Conversations/{conversation_sid}"
    return f"/Conversations/{conversation_sid}"


def list_conversations(limit: int) -> None:
    path = f"/Services/{CHAT_SERVICE_SID}/Conversations" if CHAT_SERVICE_SID else "/Conversations"
    result = api(f"{path}?{urlencode({'PageSize': limit})}")
    rows = result.get("conversations", [])
    if not rows:
        print("No conversations found. Start a chat on the site first.")
        print("If you are targeting Flex, set TWILIO_CHAT_SERVICE_SID to the Flex Conversation Service (IS...).")
        return
    print(f"{'SID':<36} {'STATE':<10} FRIENDLY NAME")
    for c in rows:
        print(f"{c.get('sid',''):<36} {c.get('state',''):<10} {c.get('friendly_name') or '-'}")


def build_options(pairs: list[str]) -> list[dict]:
    """Turn --option "Label=value" strings into the option objects the widget expects."""
    options = []
    for raw in pairs:
        label, sep, value = raw.partition("=")
        options.append({
            "uuid": str(uuid.uuid4()),
            "content": label.strip(),
            # No "=" given: reuse the label as the value that gets sent on selection.
            "value": (value.strip() if sep else label.strip()),
        })
    return options


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true", help="list conversations and exit")
    p.add_argument("--limit", type=int, default=20, help="how many conversations to list (default 20)")
    p.add_argument("--conversation", help="target conversation SID (CH...)")
    p.add_argument("--type", choices=["buttons", "dropdown", "calendar"], help="element to render")
    p.add_argument("--body", default="", help="message text shown above the element")
    p.add_argument("--option", action="append", default=[], metavar="LABEL=VALUE",
                   help="an option for buttons/dropdown; repeatable")
    p.add_argument("--label", help="placeholder text for a dropdown (dropdownLabel)")
    p.add_argument("--timezone", help="IANA timezone for a calendar, e.g. Europe/Dublin")
    p.add_argument("--author", default="bot",
                   help="message author (default 'bot'). Must NOT equal the customer's "
                        "chat identity, or the widget treats it as the visitor's own message "
                        "and renders nothing.")
    p.add_argument("--dry-run", action="store_true", help="print the request instead of sending it")
    args = p.parse_args()

    if not ACCOUNT_SID or not AUTH_TOKEN:
        print("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN first.", file=sys.stderr)
        return 1

    if args.list:
        list_conversations(args.limit)
        return 0

    if not args.conversation or not args.type:
        p.error("--conversation and --type are required (or use --list)")

    opts: dict = {"type": args.type}
    if args.type in ("buttons", "dropdown"):
        if not args.option:
            p.error(f"--type {args.type} needs at least one --option \"Label=value\"")
        opts["options"] = build_options(args.option)
        if args.type == "dropdown" and args.label:
            opts["dropdownLabel"] = args.label
    elif args.type == "calendar":
        if args.timezone:
            opts["timezone"] = args.timezone

    payload = {
        "Author": args.author,
        "Body": args.body,
        # Attributes must be a JSON *string*, not a nested object.
        "Attributes": json.dumps({"interactiveWebchatOptions": opts}),
        # Let Flex/Studio webhooks observe this message like any other.
        "X-Twilio-Webhook-Enabled": "true",
    }

    target = f"{scope(args.conversation)}/Messages"
    if args.dry_run:
        print(f"POST {API_BASE}{target}")
        print(json.dumps(payload, indent=2))
        return 0

    try:
        msg = api(target, payload)
    except HTTPError as e:
        detail = e.read().decode()[:400]
        print(f"Send failed ({e.code}): {detail}", file=sys.stderr)
        if e.code == 404 and not CHAT_SERVICE_SID:
            print("\nHint: a Flex conversation is not in the default Conversations service. "
                  "Set TWILIO_CHAT_SERVICE_SID to your Flex Conversation Service (IS...).",
                  file=sys.stderr)
        return 1

    print(f"Sent {msg.get('sid')} (index {msg.get('index')}) as '{args.author}'")
    print(f"  attributes: {msg.get('attributes')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
