from urllib.parse import urlparse, parse_qs


def extract_video_id(url):
    """Extract YouTube video ID from various URL formats."""
    if not url:
        return None

    # Handle youtu.be short links
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    # Handle youtube.com/watch?v=...
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        params = parse_qs(parsed.query)
        if "v" in params:
            return params["v"][0]
        # Handle youtube.com/embed/VIDEO_ID
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/embed/")[1].split("/")[0]

    return None
