from urllib.parse import urlparse

RETAIL_DOMAINS = {
    "amazon.com", "amazon.co.uk", "ebay.com", "homedepot.com", 
    "walmart.com", "grainger.com", "mcmaster.com", "manualslib.com",
    "scribd.com", "alibaba.com", "aliexpress.com"
}

def audit_and_fix_urls(enrichment_data: dict, research_results: list[dict], manufacturer_name: str) -> dict:
    """
    Ensures manufacturer_url is populated and valid, and that 
    the manufacturer URL or a matching domain is present in reference_urls.
    """
    if not isinstance(enrichment_data, dict):
        return enrichment_data

    mfr_url = str(enrichment_data.get("manufacturer_url", "")).strip()
    ref_urls = enrichment_data.get("reference_urls", [])
    if not isinstance(ref_urls, list):
        ref_urls = []
    
    # 1. Clean and validate existing MFR URL
    parsed_mfr = urlparse(mfr_url)
    mfr_netloc = parsed_mfr.netloc.lower()
    
    is_invalid_mfr = (
        not mfr_url 
        or any(retail in mfr_netloc for retail in RETAIL_DOMAINS)
    )

    if is_invalid_mfr and manufacturer_name:
        cleaned_manuf = str(manufacturer_name).lower().replace(" ", "")
        found_url = ""
        
        for res in research_results:
            if not isinstance(res, dict):
                continue
            url = res.get("url") or res.get("link", "")
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            
            if not netloc or any(retail in netloc for retail in RETAIL_DOMAINS):
                continue
                
            netloc_cleaned = netloc.replace("www.", "")
            if cleaned_manuf in netloc_cleaned:
                found_url = f"{parsed.scheme}://{parsed.netloc}"
                break
        
        if found_url:
            mfr_url = found_url
            enrichment_data["manufacturer_url"] = mfr_url

    # 2. Ensure manufacturer URL is represented in reference_urls
    cleaned_refs = [str(u).strip() for u in ref_urls if str(u).strip()]
    
    if mfr_url and mfr_url not in cleaned_refs:
        cleaned_refs.insert(0, mfr_url)
        
    enrichment_data["reference_urls"] = cleaned_refs[:5]
    return enrichment_data