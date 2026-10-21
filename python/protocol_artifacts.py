"""Reject a stale or mismatched protocol artifact before opening the training server."""
import hashlib
import json
from pathlib import Path

def verify_protocol_artifacts(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'dist/protocol_manifest.json').read_text())
    def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
    if manifest['authority'] != 'proto-src/src/main/proto/dispatch.proto':
        raise ValueError('unexpected authoritative proto path')
    source = root/manifest['authority']
    if source.read_bytes() != (root/'proto/dispatch.proto').read_bytes():
        raise ValueError('proto mirror differs from authoritative source')
    if sha(source) != manifest['proto_sha256']:
        raise ValueError('proto changed without regeneration')
    for path in ['dist/DRL-Dispatching-1.2.0.jar','proto-src/target/DRL-Dispatching-1.2.0.jar']:
        if sha(root/path) != manifest['jar_sha256']:
            raise ValueError(f'stale protocol JAR: {path}')
    for name, expected in manifest["python_generated_sha256"].items():
        if sha(root/"python/generated"/name) != expected:
            raise ValueError(f"stale generated Python protocol: {name}")
    return manifest
