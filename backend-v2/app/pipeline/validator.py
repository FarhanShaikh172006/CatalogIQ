from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse


class ValidationError(ValueError):
    """Raised when an enriched catalog record is invalid."""


# =========================================================
# DOMAIN CONFIGURATIONS FOR URL SELECTION
# =========================================================

RETAILER_DOMAINS = {
    "amazon.com", "ebay.com", "walmart.com", "homedepot.com", "lowes.com",
    "grainger.com", "zoro.com", "menards.com", "tractorsupply.com",
    "acehardware.com", "wayfair.com", "target.com", "bestbuy.com",
    "costco.com", "supplyhouse.com", "ferguson.com", "fastenal.com",
    "mcmaster.com", "mscindustrial.com", "acmetools.com", "northerntool.com",
}

SEARCH_ENGINE_DOMAINS = {
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
    "youtube.com", "facebook.com", "instagram.com", "linkedin.com",
    "tiktok.com", "pinterest.com",
}

AGGREGATOR_DOMAINS = {
    "wikipedia.org", "reddit.com", "manualslib.com", "datasheetpdf.com",
    "thomasnet.com", "globalspec.com", "parts-express.com",
    "ereplacementparts.com", "fix.com",
}


def _is_valid_url(value: str) -> bool:
    if not value:
        return True

    try:
        parsed = urlparse(value)
    except ValueError:
        return False

    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _is_restricted_domain(domain: str) -> bool:
    domain = (domain or "").lower().strip()
    if not domain:
        return True
    all_blocked = RETAILER_DOMAINS | SEARCH_ENGINE_DOMAINS | AGGREGATOR_DOMAINS
    return domain in all_blocked or any(domain.endswith("." + d) for d in all_blocked)


def _normalise_name(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    for char in [".", ",", "-", "_", "/", "\\", "&"]:
        text = text.replace(char, " ")
    return " ".join(text.split())


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/") if len(parsed.path) > 1 else parsed.path
        return urlunparse(("https", netloc, path, "", parsed.query, ""))
    except Exception:
        return url.strip()


# =========================================================
# URL SELECTION FUNCTION
# =========================================================

def select_best_urls(
    results: list[dict[str, Any]],
    manufacturer_name: str,
) -> tuple[str, list[str]]:
    """
    Analyzes web search results to pick the correct official
    manufacturer URL and a clean list of unique reference URLs.
    """
    manufacturer_url = ""
    reference_urls: list[str] = []
    seen_normalized_urls: set[str] = set()

    mfg_norm = _normalise_name(manufacturer_name)
    mfg_words = [
        w for w in mfg_norm.split()
        if len(w) > 2 and w not in {
            "tools", "tool", "company", "corporation", "corporate",
            "industries", "industrial", "products", "product", "inc", "corp", "llc", "co", "ltd"
        }
    ]
    primary_mfg_word = mfg_words[0] if mfg_words else ""

    # 1. Score and find the best manufacturer URL
    best_score = -1.0
    for res in results:
        url = ""
        for key in ("url", "link", "href"):
            if res.get(key):
                url = str(res[key]).strip()
                break
        
        if not url or not _is_valid_url(url):
            continue

        dom = _domain(url)
        if _is_restricted_domain(dom):
            continue

        score = 0.0
        dom_core = dom.split('.')[0].replace("-", "").replace("_", "")

        # Check if domain explicitly matches manufacturer name
        is_mfg_domain = primary_mfg_word and primary_mfg_word in dom_core
        if is_mfg_domain:
            score += 100.0

        # Check title / text relevance
        text = f"{res.get('title', '')} {res.get('snippet', '')} {res.get('description', '')}".lower()
        if mfg_norm and mfg_norm in text:
            score += 20.0

        if is_mfg_domain and score > best_score:
            best_score = score
            manufacturer_url = _normalize_url(url)

    norm_mfg_url = _normalize_url(manufacturer_url)
    mfg_domain = _domain(manufacturer_url)

    # 2. Collect unique reference URLs
    for res in results:
        url = ""
        for key in ("url", "link", "href"):
            if res.get(key):
                url = str(res[key]).strip()
                break

        if not url or not _is_valid_url(url):
            continue

        norm_url = _normalize_url(url)
        dom = _domain(url)

        # Do not include the manufacturer URL itself or other pages on the same manufacturer domain as reference
        if norm_mfg_url and norm_url == norm_mfg_url:
            continue
        if mfg_domain and dom == mfg_domain:
            continue

        if norm_url not in seen_normalized_urls:
            seen_normalized_urls.add(norm_url)
            reference_urls.append(url)

            if len(reference_urls) >= 5:
                break

    return manufacturer_url, reference_urls


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def validate_product(data: dict[str, Any]) -> list[str]:
    """
    Validate a merged catalog product.

    Returns a list of validation errors.
    An empty list means the product passed validation.
    """

    errors: list[str] = []

    # ---------------------------------------------------------
    # Required identity fields
    # ---------------------------------------------------------

    if not str(data.get("mfg_part_num", "")).strip():
        errors.append("Missing manufacturer part number.")

    if not str(data.get("manufacturer_name", "")).strip():
        errors.append("Missing manufacturer name.")

    if not str(data.get("brand_name", "")).strip():
        errors.append("Missing brand name.")

    if not str(data.get("product_name", "")).strip():
        errors.append("Missing product name.")

    # ---------------------------------------------------------
    # Attributes
    # ---------------------------------------------------------

    attributes = data.get("attributes", {})

    if not isinstance(attributes, dict):
        errors.append("Attributes must be a dictionary.")
    else:
        if len(attributes) > 15:
            errors.append(
                f"Too many attributes: {len(attributes)}. "
                "Maximum is 15."
            )

        for key, value in attributes.items():
            if not str(key).strip():
                errors.append("Attribute contains an empty key.")

            if not str(value).strip():
                errors.append(
                    f"Attribute '{key}' contains an empty value."
                )

    # ---------------------------------------------------------
    # Features
    # ---------------------------------------------------------

    features = data.get("features", [])

    if not isinstance(features, list):
        errors.append("Features must be a list.")
    else:
        if len(features) > 20:
            errors.append(
                f"Too many features: {len(features)}. "
                "Maximum is 20."
            )

        for index, feature in enumerate(features, start=1):
            if not isinstance(feature, str):
                errors.append(
                    f"Feature {index} must be a string."
                )
                continue

            if not feature.strip():
                errors.append(
                    f"Feature {index} is empty."
                )

    # ---------------------------------------------------------
    # URLs
    # ---------------------------------------------------------

    manufacturer_url = str(
        data.get("manufacturer_url", "")
    ).strip()

    if not _is_valid_url(manufacturer_url):
        errors.append(
            "Manufacturer URL is invalid."
        )

    reference_urls = data.get(
        "reference_urls",
        [],
    )

    if not isinstance(reference_urls, list):
        errors.append(
            "Reference URLs must be a list."
        )
    else:
        for url in reference_urls:
            if not isinstance(url, str):
                errors.append(
                    "Reference URL must be a string."
                )
                continue

            if not _is_valid_url(url.strip()):
                errors.append(
                    f"Invalid reference URL: {url}"
                )

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    confidence = data.get(
        "source_confidence",
        0.0,
    )

    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        errors.append(
            "Source confidence must be numeric."
        )
    else:
        if not 0.0 <= confidence_value <= 1.0:
            errors.append(
                "Source confidence must be between 0 and 1."
            )

    return errors


def validate_product_or_raise(
    data: dict[str, Any],
) -> None:
    """Validate a product and raise if invalid."""

    errors = validate_product(data)

    if errors:
        raise ValidationError(
            "Product validation failed:\n- "
            + "\n- ".join(errors)
        )