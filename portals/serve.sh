#!/bin/sh
# Serve the local (full) portals on this Mac only: http://127.0.0.1:8781
cd "$(dirname "$0")/local" && exec python3 -m http.server 8781 --bind 127.0.0.1
