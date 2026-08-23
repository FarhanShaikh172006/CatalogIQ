from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

from app.research.search_provider import SearchProvider
from app.schemas.product import Product
from app.schemas.research import WebResearchResult


class WebResearcher:
    """Research product information using Tavily web search with optimized queries and accurate metadata extraction."""

    # =========================================================
    # DOMAIN CLASSIFICATION
    # =========================================================

    RETAILER_DOMAINS = {
        "amazon.com",
        "ebay.com",
        "walmart.com",
        "homedepot.com",
        "lowes.com",
        "grainger.com",
        "zoro.com",
        "menards.com",
        "tractorsupply.com",
        "acehardware.com",
        "wayfair.com",
        "target.com",
        "bestbuy.com",
        "costco.com",
        "supplyhouse.com",
        "ferguson.com",
        "fastenal.com",
        "mcmaster.com",
        "mscindustrial.com",
        "acmetools.com",
        "northerntool.com",
    }

    SEARCH_ENGINE_DOMAINS = {
        "google.com",
        "bing.com",
        "yahoo.com",
        "duckduckgo.com",
        "youtube.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "tiktok.com",
        "pinterest.com",
    }

    AGGREGATOR_DOMAINS = {
        "wikipedia.org",
        "reddit.com",
        "manualslib.com",
        "datasheetpdf.com",
        "thomasnet.com",
        "globalspec.com",
        "parts-express.com",
        "ereplacementparts.com",
        "fix.com",
    }

    # =========================================================
    # INIT
    # =========================================================

    def __init__(self) -> None:
        self.search_provider = SearchProvider()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def research(
        self,
        product: Product,
    ) -> WebResearchResult:

        query = self._build_query(product)
        print(f"[WebResearcher] Query: {query}")

        results = self._search_web(query)
        print(f"[WebResearcher] Search results: {len(results)}")

        manufacturer_name = self._find_manufacturer_name(
            results,
            product,
        )
        print(f"[WebResearcher] Manufacturer: {manufacturer_name}")

        manufacturer_url = self._find_manufacturer_url(
            results,
            product,
            manufacturer_name,
        )
        print(f"[WebResearcher] Manufacturer URL: {manufacturer_url}")

        brand_name = self._find_brand_name(
            results,
            product,
            manufacturer_name,
        )

        trade_name = self._find_trade_name(
            results,
            product,
            brand_name,
        )

        reference_urls = self._find_reference_urls(
            results,
            manufacturer_url,
        )

        manufacturer_part_number = self._find_part_number(
            results,
            product,
        )

        sku = self._find_sku(
            results,
            product,
        )

        department = self._find_department(
            results,
            product,
        )

        product_class = self._find_class(
            results,
            product,
        )

        fine = self._find_fine(
            results,
            product,
        )

        classpath = self._build_classpath(
            department,
            product_class,
            fine,
        )

        product_name = self._find_product_name(
            results,
            product,
        )

        features = self._find_features(results)

        attributes = self._find_attributes(results)

        return WebResearchResult(
            manufacturer_url=manufacturer_url,
            reference_urls=reference_urls,

            manufacturer_name=manufacturer_name,
            part_manuf=manufacturer_name,

            brand_name=brand_name,
            trade_name=trade_name,

            manufacturer_part_number=manufacturer_part_number,
            alternate_part_number="",

            sku=sku,

            product_name=product_name,

            department=department,
            product_class=product_class,
            class_name=product_class,
            fine=fine,
            classpath=classpath,

            attributes=attributes,
            features=features,

            application=self._find_field(
                results,
                "application",
            ),

            includes=self._find_field(
                results,
                "includes",
            ),

            country_of_origin=self._find_field(
                results,
                "country_of_origin",
            ),

            source_confidence=self._calculate_confidence(
                manufacturer_url,
                manufacturer_part_number,
                sku,
                brand_name,
                department,
                product_class,
                fine,
            ),
        )

    # =========================================================
    # SEARCH QUERY
    # =========================================================

    def _build_query(
        self,
        product: Product,
    ) -> str:

        part_number = str(
            getattr(
                product,
                "mfg_part_num",
                "",
            )
            or ""
        ).strip()

        description = str(
            getattr(
                product,
                "part_desc",
                "",
            )
            or ""
        ).strip()

        parts = []
        if part_number:
            parts.append(f'"{part_number}"')
        if description:
            clean_desc = re.sub(r'[^\w\s-]', '', description)
            parts.append(clean_desc[:80])

        return " ".join(parts).strip()

    # =========================================================
    # WEB SEARCH
    # =========================================================

    def _search_web(
        self,
        query: str,
    ) -> list[dict[str, Any]]:

        if not query.strip():
            return []

        try:
            results = self.search_provider.search(
                query=query,
                limit=10,
            )

            if isinstance(results, list):
                return [
                    result
                    for result in results
                    if isinstance(result, dict)
                ]

        except Exception as exc:
            print(
                f"[WebResearcher] Search failed: {exc}"
            )

        return []

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalise_name(
        self,
        value: object,
    ) -> str:

        if value is None:
            return ""

        text = str(value).strip().lower()

        if not text:
            return ""

        replacements = {
            ".": " ",
            ",": " ",
            "-": " ",
            "_": " ",
            "/": " ",
            "\\": " ",
            "&": " and ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        suffixes = [
            " incorporated",
            " inc",
            " corporation",
            " corp",
            " company",
            " co",
            " limited",
            " ltd",
            " llc",
            " plc",
        ]

        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)]
                break

        return " ".join(text.split())

    def _normalize_url(
        self,
        url: str,
    ) -> str:

        if not url:
            return ""

        try:
            parsed = urlparse(url.strip())
            scheme = "https"
            netloc = (
                parsed.netloc
                .lower()
                .removeprefix("www.")
            )
            path = parsed.path or ""

            if len(path) > 1:
                path = path.rstrip("/")

            return urlunparse(
                (
                    scheme,
                    netloc,
                    path,
                    "",
                    parsed.query,
                    "",
                )
            )
        except Exception:
            return url.strip()

    # =========================================================
    # RESULT HELPERS
    # =========================================================

    def _result_text(
        self,
        result: dict[str, Any],
    ) -> str:

        values = [
            result.get("title", ""),
            result.get("description", ""),
            result.get("snippet", ""),
            result.get("content", ""),
            result.get("raw_content", ""),
            result.get("rawContent", ""),
            result.get("text", ""),
        ]

        return " ".join(
            str(value)
            for value in values
            if value
        )

    def _result_url(
        self,
        result: dict[str, Any],
    ) -> str:

        for key in (
            "url",
            "link",
            "href",
        ):
            value = result.get(key)

            if value:
                return str(value).strip()

        return ""

    def _domain(
        self,
        url: str,
    ) -> str:

        try:
            return (
                urlparse(url)
                .netloc
                .lower()
                .removeprefix("www.")
            )
        except Exception:
            return ""

    def _result_score(
        self,
        result: dict[str, Any],
    ) -> float:

        value = result.get("score", 0.0)

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    # =========================================================
    # KEYWORD MATCHING
    # =========================================================

    def _keyword_matches(
        self,
        text: str,
        keyword: str,
    ) -> bool:

        if not text or not keyword:
            return False

        pattern = (
            r"\b"
            + re.escape(keyword)
            + r"\b"
        )

        return re.search(pattern, text) is not None

    def _any_keyword_matches(
        self,
        text: str,
        keywords: tuple[str, ...],
    ) -> bool:

        return any(
            self._keyword_matches(text, keyword)
            for keyword in keywords
        )

    # =========================================================
    # DOMAIN HELPERS
    # =========================================================

    def _is_bad_manufacturer_domain(
        self,
        domain: str,
    ) -> bool:

        domain = (domain or "").lower().strip()
        if not domain:
            return False

        all_blocked = (
            self.RETAILER_DOMAINS
            | self.SEARCH_ENGINE_DOMAINS
            | self.AGGREGATOR_DOMAINS
        )

        if domain in all_blocked:
            return True

        return any(
            domain.endswith("." + item)
            for item in all_blocked
        )

    def _manufacturer_domain_match(
        self,
        domain: str,
        manufacturer_name: str,
    ) -> bool:

        domain = self._domain(domain)

        if not domain or not manufacturer_name:
            return False

        if self._is_bad_manufacturer_domain(domain):
            return False

        manufacturer_normalized = self._normalise_name(manufacturer_name)
        if not manufacturer_normalized:
            return False

        domain_core = domain.split('.')[0].replace("-", "").replace("_", "")
        mfg_words = [
            w for w in manufacturer_normalized.split()
            if len(w) > 2 and w not in {
                "tools", "tool", "company", "corporation",
                "corporate", "industries", "industrial",
                "products", "product", "inc", "corp", "llc", "co", "ltd"
            }
        ]

        if not mfg_words:
            return False

        primary_word = mfg_words[0]
        return primary_word in domain_core

    # =========================================================
    # MANUFACTURER
    # =========================================================

    def _find_manufacturer_name(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        for result in results:
            domain = self._domain(self._result_url(result))
            if self._is_bad_manufacturer_domain(domain):
                continue

            for key in (
                "manufacturer_name",
                "manufacturer",
                "brand_manufacturer",
                "manufacturer_brand",
            ):
                value = result.get(key)
                if value and self._valid_company_name(str(value)):
                    return str(value).strip()

        patterns = [
            r"\bmanufactured\s+by\s*[:\-]?\s*([A-Z][A-Za-z0-9&.' -]{2,60})",
            r"\bmade\s+by\s*[:\-]?\s*([A-Z][A-Za-z0-9&.' -]{2,60})",
            r"\bmanufacturer\s*[:\-]\s*([A-Z][A-Za-z0-9&.' -]{2,60})",
            r"\bmfr\s*[:\-]\s*([A-Z][A-Za-z0-9&.' -]{2,60})",
        ]

        for result in results:
            domain = self._domain(self._result_url(result))
            if self._is_bad_manufacturer_domain(domain):
                continue

            text = self._result_text(result)
            if not text:
                continue

            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if not match:
                    continue

                candidate = match.group(1).strip().rstrip(".;,")
                candidate = re.split(
                    r"\s+(?:model|mpn|part|sku|item|product)\b",
                    candidate,
                    flags=re.IGNORECASE,
                )[0].strip()

                if self._valid_company_name(candidate):
                    return candidate

        return ""

    def _valid_company_name(
        self,
        value: str,
    ) -> bool:

        value = str(value or "").strip()

        if len(value) < 2:
            return False

        invalid = {
            "unknown", "n/a", "na", "none", "manufacturer",
            "brand", "company", "retailer", "generic", "unbranded",
            "amazon", "ebay", "walmart",
        }

        if value.lower() in invalid:
            return False

        lowered = value.lower()
        if "http://" in lowered or "https://" in lowered or "www." in lowered:
            return False

        return bool(re.search(r"[A-Za-z]", value))

    # =========================================================
    # MANUFACTURER URL
    # =========================================================

    def _find_manufacturer_url(
        self,
        results: list[dict[str, Any]],
        product: Product,
        manufacturer_name: str,
    ) -> str:

        if not results:
            return ""

        for result in results:
            url = self._result_url(result)
            if not url:
                continue

            domain = self._domain(url)
            if self._manufacturer_domain_match(domain, manufacturer_name):
                return self._normalize_url(url)

        return ""

    # =========================================================
    # REFERENCE URLS
    # =========================================================

    def _find_reference_urls(
        self,
        results: list[dict[str, Any]],
        manufacturer_url: str,
    ) -> list[str]:

        urls: list[str] = []
        seen: set[str] = set()

        manufacturer_domain = self._domain(manufacturer_url)
        normalized_manufacturer_url = self._normalize_url(manufacturer_url)

        for result in results:
            url = self._result_url(result)
            if not url:
                continue

            domain = self._domain(url)
            if not domain:
                continue

            normalized_url = self._normalize_url(url)

            if normalized_manufacturer_url and normalized_url == normalized_manufacturer_url:
                continue

            if manufacturer_domain and domain == manufacturer_domain:
                continue

            if normalized_url in seen:
                continue

            seen.add(normalized_url)
            urls.append(url)

            if len(urls) >= 5:
                break

        return urls

    # =========================================================
    # BRAND
    # =========================================================

    def _find_brand_name(
        self,
        results: list[dict[str, Any]],
        product: Product,
        manufacturer_name: str,
    ) -> str:

        for result in results:
            for key in ("brand_name", "brand", "product_brand", "manufacturer_brand"):
                value = result.get(key)
                if value and self._valid_brand(str(value)):
                    return str(value).strip()

        if self._valid_brand(manufacturer_name):
            return manufacturer_name

        return str(getattr(product, "brand_name", "") or "").strip()

    def _valid_brand(
        self,
        value: str,
    ) -> bool:

        value = str(value or "").strip()
        if len(value) < 2:
            return False

        invalid = {
            "unknown", "n/a", "na", "none", "unbranded",
            "generic", "brand", "brand name", "manufacturer",
            "company", "product",
        }

        if value.lower() in invalid:
            return False

        lowered = value.lower()
        if "http://" in lowered or "https://" in lowered:
            return False

        return True

    # =========================================================
    # TRADE NAME
    # =========================================================

    def _find_trade_name(
        self,
        results: list[dict[str, Any]],
        product: Product,
        brand_name: str,
    ) -> str:

        for result in results:
            for key in (
                "trade_name", "trade", "tradeName",
                "product_line", "product_family", "series", "model_name",
            ):
                value = result.get(key)
                if value and self._valid_trade_name(str(value), brand_name):
                    return str(value).strip()

        return ""

    def _valid_trade_name(
        self,
        value: str,
        brand_name: str,
    ) -> bool:

        value = str(value or "").strip()
        if len(value) < 2:
            return False

        invalid = {
            "unknown", "n/a", "na", "none", "generic",
            "unbranded", "trade name", "product line", "model name",
        }

        if value.lower() in invalid:
            return False

        if brand_name and self._normalise_name(value) == self._normalise_name(brand_name):
            return False

        return True

    # =========================================================
    # PART NUMBER
    # =========================================================

    def _find_part_number(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        original = str(getattr(product, "mfg_part_num", "") or "").strip()
        for result in results:
            for key in ("manufacturer_part_number", "part_number", "mpn", "mfr_part_number"):
                value = result.get(key)
                if value:
                    candidate = str(value).strip()
                    if candidate:
                        return candidate

        return original

    # =========================================================
    # SKU
    # =========================================================

    def _find_sku(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        original_mpn = self._normalise_name(getattr(product, "mfg_part_num", ""))

        for result in results:
            for key in ("sku", "SKU", "product_sku", "item_sku"):
                value = result.get(key)
                if value:
                    candidate = str(value).strip()
                    if self._valid_sku(candidate) and self._normalise_name(candidate) != original_mpn:
                        return candidate

        patterns = [
            r"\bSKU\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",
            r"\bItem\s*(?:No|Number|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",
            r"\bCatalog\s*(?:No|Number|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",
        ]

        for result in results:
            text = self._result_text(result)
            for pattern in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    candidate = match.group(1).strip()
                    if not self._valid_sku(candidate):
                        continue
                    if self._normalise_name(candidate) == original_mpn:
                        continue
                    return candidate

        return ""

    def _valid_sku(
        self,
        value: str,
    ) -> bool:

        value = str(value or "").strip()
        if len(value) < 3:
            return False

        if value.lower() in {
            "n/a", "na", "none", "unknown",
            "null", "sku", "item", "number",
        }:
            return False

        return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value))

    # =========================================================
    # CLASSIFICATION
    # =========================================================

    def _combined_product_text(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        return self._normalise_name(
            " ".join(
                [
                    str(getattr(product, "part_desc", "") or ""),
                    *[self._result_text(result) for result in results],
                ]
            )
        )

    def _find_department(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        value = self._find_classification_field(results, ("department", "dept"))
        if value:
            return value

        text = self._combined_product_text(results, product)

        rules = [
            ("Appliance", ("appliance", "refrigerator", "fridge", "dishwasher", "range", "oven", "microwave", "washer", "dryer")),
            ("Electrical", ("electrical", "switch", "outlet", "receptacle", "breaker", "circuit", "wire", "cable", "connector")),
            ("Plumbing", ("plumbing", "faucet", "valve", "pipe", "drain", "toilet", "shower", "sink", "hose")),
            ("HVAC", ("hvac", "air conditioner", "heating", "furnace", "heat pump", "thermostat", "ventilation")),
            ("Tools", ("tool", "drill", "saw", "hammer", "wrench", "screwdriver", "grinder", "plier")),
            ("Hardware", ("hardware", "bolt", "screw", "nut", "washer", "fastener", "hinge", "bracket")),
            ("Safety", ("safety", "protective", "ppe", "respirator", "helmet", "hard hat")),
            ("Clothing", ("clothing", "apparel", "shirt", "pants", "jacket", "shoe", "glove")),
            ("Food", ("food", "snack", "beverage", "drink", "coffee", "tea", "candy")),
        ]

        for department, keywords in rules:
            if self._any_keyword_matches(text, keywords):
                return department

        return ""

    def _find_class(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        value = self._find_classification_field(results, ("product_class", "class_name", "class"))
        if value:
            return value

        text = self._combined_product_text(results, product)

        rules = [
            ("Large Appliance", ("refrigerator", "fridge", "freezer", "dishwasher", "range", "oven", "washer", "dryer")),
            ("Small Appliance", ("microwave", "coffee maker", "toaster", "blender", "mixer", "air fryer")),
            ("Electrical Components", ("switch", "receptacle", "outlet", "breaker", "relay", "contactor", "connector")),
            ("Power Tools", ("drill", "grinder", "saw", "driver", "impact wrench")),
            ("Hand Tools", ("hammer", "wrench", "screwdriver", "pliers", "ratchet", "socket")),
            ("Fasteners", ("bolt", "screw", "nut", "washer", "fastener", "anchor")),
            ("Plumbing Fixtures", ("faucet", "sink", "toilet", "shower", "drain")),
            ("HVAC Equipment", ("air conditioner", "furnace", "heat pump", "condenser")),
            ("Safety Equipment", ("helmet", "hard hat", "respirator", "safety glasses")),
        ]

        for class_name, keywords in rules:
            if self._any_keyword_matches(text, keywords):
                return class_name

        return ""

    def _find_fine(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        value = self._find_classification_field(results, ("fine", "product_type"))
        if value:
            return value

        text = self._combined_product_text(results, product)

        rules = [
            ("Refrigerator", ("refrigerator", "fridge")),
            ("Dishwasher", ("dishwasher",)),
            ("Oven", ("wall oven", "oven")),
            ("Range", ("cooking range", "range")),
            ("Microwave", ("microwave",)),
            ("Washer", ("washing machine", "washer")),
            ("Dryer", ("dryer",)),
            ("Freezer", ("freezer",)),
            ("Switch", ("switch",)),
            ("Receptacle", ("receptacle", "outlet")),
            ("Circuit Breaker", ("circuit breaker", "breaker")),
            ("Relay", ("relay",)),
            ("Connector", ("connector",)),
            ("Drill", ("drill",)),
            ("Grinder", ("grinder",)),
            ("Saw", ("circular saw", "reciprocating saw", "jigsaw", "saw")),
            ("Wrench", ("wrench",)),
            ("Screwdriver", ("screwdriver", "driver")),
            ("Bolt", ("bolt",)),
            ("Screw", ("screw",)),
            ("Faucet", ("faucet",)),
            ("Valve", ("valve",)),
            ("Safety Helmet", ("hard hat", "safety helmet", "helmet")),
            ("Safety Glasses", ("safety glasses", "protective eyewear")),
        ]

        for product_type, keywords in rules:
            if self._any_keyword_matches(text, keywords):
                return product_type

        return ""

    def _find_classification_field(
        self,
        results: list[dict[str, Any]],
        keys: tuple[str, ...],
    ) -> str:

        for result in results:
            for key in keys:
                value = result.get(key)
                if value:
                    text = str(value).strip()
                    if text:
                        return text

        return ""

    def _build_classpath(
        self,
        department: str,
        product_class: str,
        fine: str,
    ) -> str:

        return " > ".join(
            value.strip()
            for value in (
                department,
                product_class,
                fine,
            )
            if value and value.strip()
        )

    # =========================================================
    # PRODUCT NAME
    # =========================================================

    def _find_product_name(
        self,
        results: list[dict[str, Any]],
        product: Product,
    ) -> str:

        for result in results:
            value = result.get("product_name")
            if value:
                return str(value).strip()

        for result in results:
            title = result.get("title")
            if title:
                return str(title).strip()

        return str(getattr(product, "part_desc", "") or "").strip()

    # =========================================================
    # FEATURES
    # =========================================================

    def _find_features(
        self,
        results: list[dict[str, Any]],
    ) -> list[str]:

        features: list[str] = []
        seen: set[str] = set()

        for result in results:
            values = result.get("features", [])
            if isinstance(values, str):
                values = [values]

            if not isinstance(values, list):
                continue

            for value in values:
                text = str(value).strip()
                if not text:
                    continue

                normalized = " ".join(text.lower().split())
                if normalized in seen:
                    continue

                seen.add(normalized)
                features.append(text)

                if len(features) >= 8:
                    return features

        return features

    # =========================================================
    # ATTRIBUTES
    # =========================================================

    def _find_attributes(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, str]:

        attributes: dict[str, str] = {}

        for result in results:
            values = result.get("attributes", {})
            if not isinstance(values, dict):
                continue

            for key, value in values.items():
                key_text = str(key).strip()
                value_text = str(value).strip()

                if key_text and value_text and key_text not in attributes:
                    attributes[key_text] = value_text

                if len(attributes) >= 22:
                    return attributes

        return attributes

    # =========================================================
    # GENERIC FIELD
    # =========================================================

    def _find_field(
        self,
        results: list[dict[str, Any]],
        field: str,
    ) -> str:

        for result in results:
            value = result.get(field)
            if value:
                return str(value).strip()

        return ""

    # =========================================================
    # CONFIDENCE
    # =========================================================

    def _calculate_confidence(
        self,
        manufacturer_url: str,
        manufacturer_part_number: str,
        sku: str,
        brand_name: str,
        department: str,
        product_class: str,
        fine: str,
    ) -> float:

        score = 0.0

        if manufacturer_url:
            score += 0.25

        if manufacturer_part_number:
            score += 0.20

        if sku:
            score += 0.15

        if brand_name:
            score += 0.15

        if department:
            score += 0.10

        if product_class:
            score += 0.10

        if fine:
            score += 0.05

        return round(
            min(score, 1.0),
            2,
        )