"""
CanaryFile Engine - CLI Document Injector
Command line tool to generate weaponized decoy files with embedded canary triggers.
"""

import argparse
import sys
import uuid
import os
import httpx
from typing import Optional

from generator.pdf_injector import PDFCanaryInjector


def register_token_remote(server_url: str, token_id: str, label: str, file_type: str):
    """Attempt to register token with the listener server API."""
    api_endpoint = f"{server_url.rstrip('/')}/api/v1/tokens"
    payload = {
        "token_id": token_id,
        "label": label,
        "file_type": file_type
    }
    try:
        response = httpx.post(api_endpoint, json=payload, timeout=3.0)
        if response.status_code == 201:
            print(f"[+] Token registered successfully on listener server: {token_id}")
        else:
            print(f"[!] Server returned status {response.status_code} during token registration.")
    except Exception as e:
        print(f"[*] Note: Could not contact listener server at {server_url} to register token directly ({e}). Token will log on hit if server is running.")


def main():
    parser = argparse.ArgumentParser(
        description="CanaryFile Engine - Active Defense Document Injector CLI"
    )
    
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8000",
        help="Base URL of CanaryFile listener server (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--type",
        choices=["pdf"],
        default="pdf",
        help="Target document type to generate/inject (default: pdf)"
    )
    parser.add_argument(
        "--input",
        help="Path to an existing input file to inject. If omitted, a new decoy document will be created."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output filepath for weaponized canary file."
    )
    parser.add_argument(
        "--token",
        help="Custom token ID. If omitted, a unique UUID string will be generated."
    )
    parser.add_argument(
        "--label",
        default="",
        help="Descriptive label or memo for tracking (e.g., 'Financial_Q3_Draft.pdf')"
    )

    args = parser.parse_args()

    token_id = args.token or str(uuid.uuid4())
    print("=" * 60)
    print(" CANARYFILE ENGINE - DOCUMENT GENERATOR ")
    print("=" * 60)
    print(f"[*] Target Listener URL : {args.server}")
    print(f"[*] Document Type        : {args.type.upper()}")
    print(f"[*] Token ID             : {token_id}")
    print(f"[*] Label / Memo         : {args.label or 'N/A'}")
    print(f"[*] Output Path          : {args.output}")

    # Register token on listener server
    register_token_remote(args.server, token_id, args.label, args.type)

    injector = PDFCanaryInjector(listener_url=args.server)

    if args.type == "pdf":
        if args.input:
            if not os.path.exists(args.input):
                print(f"[!] Error: Input file '{args.input}' does not exist.")
                sys.exit(1)
            print(f"[*] Injecting tracking payload into existing PDF '{args.input}'...")
            injector.inject_pdf(args.input, args.output, token_id=token_id)
        else:
            print("[*] Generating new decoy canary PDF...")
            injector.create_canary_pdf(args.output, token_id=token_id, title=args.label or "Confidential")

    print("\n[+] SUCCESS: Canary document successfully generated!")
    print(f"[->] File location  : {os.path.abspath(args.output)}")
    print(f"[->] Trigger URL    : {args.server.rstrip('/')}/t/{token_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
