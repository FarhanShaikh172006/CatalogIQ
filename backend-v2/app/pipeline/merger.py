import re
from typing import Any
from urllib.parse import urlparse

from app.schemas.product import Product
from app.schemas.research import WebResearchResult


# ============================================================
# BASIC HELPERS
# ============================================================

def _is_meaningful(value: Any) -> str:
    """Check if a value is non-empty and contains actual data."""
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    null_equivalents = {"n/a", "na", "none", "unknown", "null", "tbd", "-", ".", "undefined"}
    if text.lower() in null_equivalents:
        return ""

    return text


def _first_non_empty(*values: Any) -> str:
    """Return the first meaningful non-empty value."""
    for value in values:
        text = _is_meaningful(value)
        if text:
            return text
    return ""


def _clean_url(value: Any) -> str:
    """Normalize a URL string."""
    if value is None:
        return ""

    url = str(value).strip().strip(" <>\"'")
    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    return url


def _url_domain(url: str) -> str:
    """Return normalized hostname without 'www.'."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _is_allowed_domain(url: str) -> bool:
    """
    Reject obvious marketplace, distributor, B2B, and search domains.
    If a URL is from these domains, it is NEVER the manufacturer.
    """
    domain = _url_domain(url)
    if not domain:
        return False

    blocked_domains = {
        # Search / Social / Wiki
        "google.com", "google.co.in", "bing.com", "yahoo.com", "duckduckgo.com",
        "facebook.com", "instagram.com", "linkedin.com", "youtube.com", "reddit.com",
        "pinterest.com", "wikipedia.org",
        
        # Major Retailers & Marketplaces
        "amazon.com", "amazon.in", "amazon.co.uk", "ebay.com", "ebay.in",
        "walmart.com", "target.com", "homedepot.com", "lowes.com", "bestbuy.com",
        "wayfair.com", "alibaba.com", "aliexpress.com", "etsy.com", "sears.com",
        
        # Industrial / B2B / Components Distributors
        "grainger.com", "mcmaster.com", "zoro.com", "fastenal.com", "mscdirect.com",
        "uline.com", "globalindustrial.com", "webstaurantstore.com", "partstown.com", 
        "supplyhouse.com", "acmetools.com", "ferguson.com", "tractorsupply.com",
        "digikey.com", "mouser.com", "arrow.com", "farnell.com", "rs-online.com", 
        "newark.com", "avnet.com", "futureelectronics.com", "cdw.com", "bhphotovideo.com",
        
        # B2B Sourcing Catalogs
        "thomasnet.com", "directindustry.com", "made-in-china.com", "globalsources.com",
        
        # Manuals / SaaS
        "shopify.com", "manualslib.com", "issuu.com"
    }

    if domain in blocked_domains:
        return False

    if any(domain.endswith("." + blocked) for blocked in blocked_domains):
        return False

    lowered_url = url.lower()
    bad_path_terms = (
        "/search", "?q=", "?query=", "?keyword=", "/results", 
        "/product-search", "/catalog-search", "/shopping"
    )

    if any(term in lowered_url for term in bad_path_terms):
        return False

    return True


# ============================================================
# MANUFACTURER URL SELECTION
# ============================================================

def _select_manufacturer_url(
    research: WebResearchResult,
    manufacturer_name: str,
    brand_name: str,
) -> str:
    """
    Selects the official manufacturer URL.
    Actively hunts through `reference_urls` for a domain that matches 
    the brand/manufacturer name while avoiding known distributors.
    """
    candidates: list[str] = []

    # 1. Grab the primary suggested URL
    primary_url = _clean_url(getattr(research, "manufacturer_url", ""))
    if primary_url:
        candidates.append(primary_url)

    # 2. Append all reference URLs
    refs = getattr(research, "reference_urls", [])
    if isinstance(refs, list):
        for ref in refs:
            cleaned = _clean_url(ref)
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)

    if not candidates:
        return ""

    # Normalize names for domain matching (strip everything except alphanumeric)
    mfr_norm = "".join(c for c in str(manufacturer_name).lower() if c.isalnum())
    brand_norm = "".join(c for c in str(brand_name).lower() if c.isalnum())

    valid_candidates = []

    for url in candidates:
        if not _is_allowed_domain(url):
            continue

        domain = _url_domain(url)
        # Get just the core domain name (e.g., "sony" from "sony.com")
        domain_body = domain.split(".")[0] 

        # STRONG MATCH: Does the domain contain the brand/mfr name? 
        # (or vice versa, for abbreviations like "General Electric" -> "ge")
        is_match = False
        if mfr_norm and len(mfr_norm) >= 2:
            if mfr_norm in domain_body or domain_body in mfr_norm:
                is_match = True
        if brand_norm and len(brand_norm) >= 2:
            if brand_norm in domain_body or domain_body in brand_norm:
                is_match = True

        if is_match:
            return url  # Return the very first strong match we find!

        # Keep as a fallback if it passed the blocklist
        if url == primary_url:
            valid_candidates.append(url)

    # If no reference URL strongly matched the brand, but the primary URL 
    # wasn't a blocked distributor, use it as a fallback.
    if valid_candidates:
        return valid_candidates[0]

    return ""


# ============================================================
# REFERENCE URL SELECTION
# ============================================================

def _build_reference_urls(
    research: WebResearchResult,
    manufacturer_url: str,
) -> list[str]:
    """Build clean reference URL list, omitting the selected MFR URL."""
    reference_urls: list[str] = []
    research_reference_urls = getattr(research, "reference_urls", [])

    if not isinstance(research_reference_urls, list):
        return []

    manufacturer_normalized = manufacturer_url.rstrip("/").lower() if manufacturer_url else ""
    seen: set[str] = set()

    for url in research_reference_urls:
        cleaned = _clean_url(url)
        if not cleaned:
            continue

        normalized = cleaned.rstrip("/").lower()
        if manufacturer_normalized and normalized == manufacturer_normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        reference_urls.append(cleaned)

        if len(reference_urls) >= 5:
            break

    return reference_urls


# ============================================================
# ATTRIBUTES & FEATURES
# ============================================================

def _merge_attributes(research_attributes: dict[str, str], ai_attributes: dict[str, Any]) -> dict[str, str]:
    merged: dict[str, str] = {}
    seen_keys_lower: set[str] = set()

    for key, value in ai_attributes.items():
        key_text, value_text = str(key).strip(), _is_meaningful(value)
        if key_text and value_text:
            merged[key_text] = value_text
            seen_keys_lower.add(key_text.lower())

    for key, value in research_attributes.items():
        key_text, value_text = str(key).strip(), _is_meaningful(value)
        if key_text and value_text:
            key_lower = key_text.lower()
            if key_lower in seen_keys_lower and key_text not in merged:
                existing_key = next((ek for ek in merged if ek.lower() == key_lower), None)
                if existing_key:
                    del merged[existing_key]
            merged[key_text] = value_text
            seen_keys_lower.add(key_lower)

    return merged

def _merge_features(research_features: list[str], ai_features: list[Any]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for feature in [*research_features, *ai_features]:
        text = _is_meaningful(feature)
        if not text:
            continue
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = " ".join(normalized.split())
        if normalized in seen:
            continue
        seen.add(normalized)
        merged.append(text)

    return merged[:20]


# ============================================================
# MAIN MERGER
# ============================================================

def merge_product(
    product: Product,
    research: WebResearchResult,
    enrichment: dict[str, Any],
) -> dict[str, Any]:
    
    # 1. Determine Brand & Manufacturer First (Needed for URL matching)
    manufacturer_name = _first_non_empty(
        getattr(research, "manufacturer_name", ""),
        getattr(product, "manufacturer_name", ""),
        getattr(product, "part_manuf", ""),
    )

    part_manuf = _first_non_empty(
        getattr(research, "part_manuf", ""),
        manufacturer_name,
        getattr(product, "part_manuf", ""),
    )

    brand_name = _first_non_empty(
        getattr(research, "brand_name", ""),
        getattr(product, "brand_name", ""),
        getattr(product, "e1_brand", ""),
    )

    # 2. Extract URLs (Now actively scans reference_urls for brand matches)
    manufacturer_url = _select_manufacturer_url(
        research=research,
        manufacturer_name=manufacturer_name,
        brand_name=brand_name,
    )

    reference_urls = _build_reference_urls(
        research=research,
        manufacturer_url=manufacturer_url,
    )

    # 3. Merge Complex Data
    research_attrs = getattr(research, "attributes", {}) if isinstance(getattr(research, "attributes", {}), dict) else {}
    ai_attrs = enrichment.get("attributes", {}) if isinstance(enrichment.get("attributes", {}), dict) else {}
    attributes = _merge_attributes(research_attrs, ai_attrs)

    research_feats = getattr(research, "features", []) if isinstance(getattr(research, "features", []), list) else []
    ai_feats = enrichment.get("features", []) if isinstance(enrichment.get("features", []), list) else []
    features = _merge_features(research_feats, ai_feats)

    # 4. Strings & Identifiers
    department = _first_non_empty(getattr(research, "department", ""))
    product_class = _first_non_empty(getattr(research, "class_name", ""), getattr(research, "product_class", ""))
    fine = _first_non_empty(getattr(research, "fine", ""))

    classpath = _first_non_empty(getattr(research, "classpath", ""))
    if not classpath:
        classpath = " > ".join(part for part in [department, product_class, fine] if part)

    manufacturer_part_number = _first_non_empty(
        getattr(research, "manufacturer_part_number", ""),
        getattr(product, "manufacturer_part_number", ""),
        getattr(product, "mfg_part_num", ""),
    )

    product_name = _first_non_empty(
        enrichment.get("product_name", ""),
        getattr(research, "product_name", ""),
        getattr(product, "part_desc", ""),
    )

    # 5. Build Result
    return {
        "row_number": getattr(product, "row_number", None),

        "mfg_part_num": _first_non_empty(getattr(product, "mfg_part_num", "")),
        "part_desc": _first_non_empty(getattr(product, "part_desc", "")),

        "part_number": manufacturer_part_number,
        "department": department,
        "product_class": product_class,
        "class_name": product_class,
        "fine": fine,
        "sku": _first_non_empty(getattr(research, "sku", "")),
        "part_manuf": part_manuf,
        "manufacturer_name": manufacturer_name,
        "brand_name": brand_name,
        "classpath": classpath,

        "trade_name": _first_non_empty(getattr(research, "trade_name", ""), brand_name),
        "manufacturer_part_number": manufacturer_part_number,
        "alternate_part_number": _first_non_empty(getattr(research, "alternate_part_number", "")),
        "product_name": product_name,

        "mobile_description": _is_meaningful(enrichment.get("mobile_description", "")),
        "invoice_description": _is_meaningful(enrichment.get("invoice_description", "")),
        "short_description": _is_meaningful(enrichment.get("short_description", "")),
        "long_description": _is_meaningful(enrichment.get("long_description", "")),
        "retail_description": _is_meaningful(enrichment.get("retail_description", "")),
        "marketing_description": _is_meaningful(enrichment.get("marketing_description", "")),

        "attributes": attributes,
        "features": features,

        "application": _first_non_empty(getattr(research, "application", ""), enrichment.get("application", "")),
        "includes": _first_non_empty(getattr(research, "includes", ""), enrichment.get("includes", "")),
        "country_of_origin": _first_non_empty(getattr(research, "country_of_origin", "")),

        "manufacturer_url": manufacturer_url,
        "reference_urls": reference_urls,
        "source_confidence": getattr(research, "source_confidence", 0),
    }