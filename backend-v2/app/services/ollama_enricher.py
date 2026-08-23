import json

from app.schemas.product import Product
from app.services.ollama_provider import OllamaProvider


class ProductEnricher:
    """Generate structured catalog content from verified product research."""

    REQUIRED_FIELDS = {
        "mobile_description",
        "invoice_description",
        "short_description",
        "long_description",
        "retail_description",
        "marketing_description",
        "product_name",
        "features",
        "attributes",
        "application",
        "includes",
    }

    def __init__(
        self,
        provider: OllamaProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()

    def enrich(
        self,
        product: Product,
        research: dict,
    ) -> dict:
        prompt = self._build_prompt(product, research)

        response = self.provider.generate(
            prompt,
            json_mode=True,
        )

        return self._parse_response(response)

    def _build_prompt(
        self,
        product: Product,
        research: dict,
    ) -> str:
        research_json = json.dumps(
            research,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return f"""
Return ONLY one valid JSON object.

Do not write explanations.
Do not write markdown.
Do not write reasoning.
Do not write commentary.
Do not use a JSON array as the root.
Use null or an empty string when information is not verified.
Never invent specifications.

PRODUCT:
MPN: {product.mfg_part_num}
Description: {product.part_desc}
Manufacturer: {product.part_manuf}
Brand: {product.brand_name}

VERIFIED WEB RESEARCH:
{research_json}

Create catalog enrichment using ONLY the verified information above.

Rules:
- product_name: clean factual product name.
- Descriptions must be concise and factual.
- features: 5 to 8 useful English sentences.
- attributes: technical key-value specifications only.
- Maximum 15 attributes.
- application: verified intended use.
- includes: verified package contents.
- Do not invent dimensions, materials, quantities, ratings, compatibility, or specifications.
- Do not include prices, reviews, search-result titles, navigation text, or unrelated metadata.
- Do not repeat the same information unnecessarily.

Return EXACTLY this JSON structure:

{{
  "mobile_description": "",
  "invoice_description": "",
  "short_description": "",
  "long_description": "",
  "retail_description": "",
  "marketing_description": "",
  "product_name": "",
  "features": [],
  "attributes": {{}},
  "application": "",
  "includes": ""
}}
""".strip()

    def _parse_response(
        self,
        response: str,
    ) -> dict:
        response = response.strip()

        # Remove accidental markdown fences.
        if response.startswith("```"):
            response = response.replace("```json", "", 1)
            response = response.replace("```", "")
            response = response.strip()

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Product enricher returned invalid JSON.\n"
                f"Response:\n{response}"
            ) from exc

        if not isinstance(data, dict):
            raise TypeError(
                "Product enricher returned a non-object JSON response."
            )

        # Ensure all expected fields exist.
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                if field == "features":
                    data[field] = []
                elif field == "attributes":
                    data[field] = {}
                else:
                    data[field] = ""

        # Normalize features.
        if not isinstance(data["features"], list):
            data["features"] = [str(data["features"])]

        data["features"] = [
            str(feature).strip()
            for feature in data["features"]
            if str(feature).strip()
        ][:8]

        # Normalize attributes.
        if not isinstance(data["attributes"], dict):
            data["attributes"] = {}

        data["attributes"] = {
            str(key).strip(): str(value).strip()
            for key, value in data["attributes"].items()
            if str(key).strip() and str(value).strip()
        }

        # Limit attributes.
        data["attributes"] = dict(
            list(data["attributes"].items())[:15]
        )

        return data