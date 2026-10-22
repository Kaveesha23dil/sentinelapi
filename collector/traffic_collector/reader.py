"""Only read immutable sanitized spool chunks, bounded by the trusted bridge."""
import json
import re


def chunks(directory, completed):
    read_count = 0
    for path in sorted(directory.glob('*.ndjson')):
        if not re.fullmatch(r'[a-f0-9]{64}\.ndjson', path.name) or path.name in completed:
            continue
        if read_count >= 100:
            break
        read_count += 1
        if path.is_symlink() or path.stat().st_size > 131072:
            raise ValueError('Unsafe spool file')
        lines = path.read_text(errors='replace').splitlines()
        if len(lines) > 1000:
            raise ValueError('Oversized spool chunk')
        flows = []
        for line in lines:
            try:
                flows.append(json.loads(line))
            except (ValueError, RecursionError):
                continue
        yield path.name, flows
