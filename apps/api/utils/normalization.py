import urllib.parse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "mc_cid",
    "mc_eid",
}


def normalize_url(url: str | None) -> str | None:
    """
    Normalizes a URL by removing common tracking parameters.
    """
    if not url:
        return url

    try:
        parsed = urllib.parse.urlparse(url)

        # If there's no scheme or netloc, it might be a partial/invalid URL
        if not parsed.scheme or not parsed.netloc:
            return url

        # Parse query string
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

        # Filter out tracking parameters
        filtered_params = [
            (k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS
        ]

        # Reconstruct query
        new_query = urllib.parse.urlencode(filtered_params)

        # Reconstruct URL
        normalized_parsed = parsed._replace(query=new_query)
        return urllib.parse.urlunparse(normalized_parsed)

    except Exception:
        # Fallback to original if parsing fails
        return url


def normalize_domain(domain: str | None, url: str | None = None) -> str | None:
    """
    Normalizes a domain string (lowercasing, stripping www. and ports).
    If domain is missing, attempts to extract it from the URL.
    """
    target_domain = domain

    if not target_domain and url:
        try:
            parsed = urllib.parse.urlparse(url)
            target_domain = parsed.netloc
        except Exception:
            pass

    if not target_domain:
        return None

    # Lowercase
    target_domain = target_domain.lower()

    # Strip port if present
    target_domain = target_domain.split(":")[0]

    # Strip leading www.
    if target_domain.startswith("www."):
        target_domain = target_domain[4:]

    return target_domain


SEARCH_QUERY_KEYS = {"q", "query", "search", "search_query", "keyword", "term", "k", "p", "as_q"}


def extract_url_search_params(url: str | None) -> str | None:
    """
    Extracts search query string from URL query parameters (e.g. q, query, search, term).
    URL-decodes the parameter value and returns normalized query text.
    """
    if not url:
        return None

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.query:
            return None

        query_params = urllib.parse.parse_qs(parsed.query)
        for key, values in query_params.items():
            if key.lower() in SEARCH_QUERY_KEYS:
                for val in values:
                    val_str = val.strip()
                    if val_str:
                        decoded = urllib.parse.unquote_plus(val_str)
                        if decoded.strip():
                            return decoded.strip()
    except Exception:
        pass

    return None

