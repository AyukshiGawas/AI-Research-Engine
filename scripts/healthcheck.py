import sys
from urllib.request import urlopen

urls = [
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/api/v1/version",
]

for url in urls:
    try:
        with urlopen(url, timeout=5) as response:
            print(f"{url} -> {response.status}")
    except Exception as exc:  # pragma: no cover
        print(f"{url} -> ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
