#!/bin/bash
exec "$AUDIT_PYTHON" -B -m pytest "$@"
