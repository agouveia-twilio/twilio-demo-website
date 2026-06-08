#!/usr/bin/env python3
"""
Segment Profile API proxy server.
Runs on port 3001. Set env vars before starting:

    export SEGMENT_SPACE_ID=spa_acdDFfuQCJp4TWzw9cKZfn
    export SEGMENT_ACCESS_TOKEN=YPQuFPUFfvq5Cxm89wXvB8psZ6OganFJhyH7H78V66y4UP96g2IIdq5td_DGqBTalj1w9TjPnoikOjjno7suOi3iI1_UvzCpfu8vpa9W7a1Bgsg6AVBdX9WFj3SlWztb1W7tep_Nn_5Civ6hLEi7pIre-psAx7GprtuMAlhmTwskMESMPpc0hg5FCk2dozUgst0rVofprvfIvYHPfuRRxgwZ-bYhQ_mI03qX2uVsqsq142YhwxkFY9YJuKTN5MJSvRpD-XNZF5N9xlBxp-iBOvnWUPU=
    python server.py
"""

import json
import os
import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

PORT = 3001
SPACE_ID = os.environ.get("SEGMENT_SPACE_ID", "")
ACCESS_TOKEN = os.environ.get("SEGMENT_ACCESS_TOKEN", "")
PROFILE_API_BASE = "https://profiles.segment.com/v1/spaces"

# CORS headers sent on every response
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def profile_api_get(path: str) -> dict:
    """Call the Segment Profile API with Basic Auth. Returns parsed JSON."""
    url = f"{PROFILE_API_BASE}/{SPACE_ID}{path}"
    token_b64 = base64.b64encode(f"{ACCESS_TOKEN}:".encode()).decode()
    req = Request(url, headers={"Authorization": f"Basic {token_b64}"})
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def send_json(self, status: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode()
        params = {k: v[0] for k, v in parse_qs(raw).items()}
        path = urlparse(self.path).path

        if path == "/segment-profile-api":
            self._handle_login(params)
        elif path == "/segment-profile-traits":
            self._handle_traits(params)
        else:
            self.send_json(404, {"error": "Not found"})

    def _handle_login(self, params: dict):
        """
        POST /segment-profile-api
        Body: email=<email>&userId=<userId>

        Looks up the profile by email in Segment, then checks whether the
        userId stored on that profile matches the one provided.

        Returns:
          200  { success: true,  match: true }
          403  { success: false, match: false, message: "..." }   — userId mismatch
          404  { success: false, message: "..." }                  — email not found
        """
        email = params.get("email", "").strip()
        user_id = params.get("userId", "").strip()

        if not email or not user_id:
            self.send_json(400, {"success": False, "message": "email and userId are required"})
            return

        external_id = f"email:{quote(email)}"
        try:
            data = profile_api_get(
                f"/collections/users/profiles/{external_id}/external_ids"
            )
        except HTTPError as e:
            if e.code == 404:
                self.send_json(404, {"success": False, "message": f"Email '{email}' not found"})
            else:
                self.send_json(502, {"success": False, "message": f"Profile API error: {e.code}"})
            return

        # Find the user_id external_id entry
        identities = data.get("data", [])
        stored_user_id = None
        for entry in identities:
            if entry.get("type") == "user_id":
                stored_user_id = entry.get("id")
                break

        if stored_user_id is None:
            # Profile exists by email but has no userId — treat as mismatch
            self.send_json(403, {
                "success": False,
                "match": False,
                "message": "No user_id found on this profile",
            })
            return

        if stored_user_id == user_id:
            self.send_json(200, {"success": True, "match": True})
        else:
            self.send_json(403, {
                "success": False,
                "match": False,
                "message": f"User ID does not match the profile for '{email}'",
            })

    def _handle_traits(self, params: dict):
        """
        POST /segment-profile-traits
        Body: externalId=<user_id:abc | anonymous_id:abc>&traits=last_item_searched

        Fetches traits from the Segment Profile API for the given identifier.

        Returns:
          200  { traits: { last_item_searched: "..." } }
          404  { traits: {} }   — profile not found
        """
        external_id = params.get("externalId", "").strip()
        trait_names = params.get("traits", "last_item_searched").strip()

        if not external_id:
            self.send_json(400, {"error": "externalId is required"})
            return

        try:
            data = profile_api_get(
                f"/collections/users/profiles/{quote(external_id)}/traits"
                f"?include={quote(trait_names)}"
            )
            self.send_json(200, {"traits": data.get("traits", {})})
        except HTTPError as e:
            if e.code == 404:
                self.send_json(200, {"traits": {}})
            else:
                self.send_json(502, {"error": f"Profile API error: {e.code}"})


if __name__ == "__main__":
    if not SPACE_ID or not ACCESS_TOKEN:
        print("❌  Set SEGMENT_SPACE_ID and SEGMENT_ACCESS_TOKEN before starting.")
        raise SystemExit(1)

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✅  Segment proxy running on http://localhost:{PORT}")
    print(f"    Space ID:     {SPACE_ID}")
    print(f"    Access Token: {ACCESS_TOKEN[:6]}{'*' * (len(ACCESS_TOKEN) - 6)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
