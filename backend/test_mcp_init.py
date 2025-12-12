#!/usr/bin/env python3
import json
import sys

# Simulate what Claude Desktop sends
init_msg = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {
            "name": "claude-ai",
            "version": "0.1.0"
        }
    },
    "id": 0
}

print(json.dumps(init_msg), file=sys.stderr)
print(json.dumps(init_msg))
