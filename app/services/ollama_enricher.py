import json



from app.schemas.product import Product

from app.services.ollama_provider import OllamaProvider





class ProductEnricher:

    """Generate catalog-ready content from verified product research."""



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

You are a catalog data formatter.



Use ONLY the supplied product data and VERIFIED WEB RESEARCH.



Never invent specifications.

Never assume missing information.

Never copy search-result metadata.



PRODUCT:



MPN: {product.mfg_part_num}

Description: {product.part_desc}

Manufacturer: {product.part_manuf}

Brand: {product.brand_name}



VERIFIED WEB RESEARCH:



{research_json}



Create concise, factual catalog content.



CRITICAL OUTPUT RULES:



- Return exactly ONE JSON OBJECT.

- The response MUST start with {{ and end with }}.

- NEVER return a JSON array as the root response.

- NEVER return markdown.

- NEVER return explanations.

- NEVER return search-result titles.

- NEVER return search-result headings.

- NEVER copy source text.

- Do not invent specifications.

- Maximum 8 features.

- Maximum 15 attributes.

- Features must be useful English sentences.

- Attributes must contain technical product specifications.

- Use verified research whenever available.

- Do not repeat the original Part Description in every field.



DESCRIPTION FIELDS:



mobile_description:

Very short product description.



invoice_description:

Short professional invoice description.



short_description:

Concise catalog description including important verified specifications.



long_description:

Detailed factual product description using verified information.



retail_description:

Customer-friendly explanation of the product.



marketing_description:

Professional benefit-focused description using only verified facts.



product_name:

Clean product name without unnecessary repetition.



FEATURES:



Create 5-8 useful English sentences.



Focus on:

- construction

- materials

- specifications

- compatibility

- intended use

- useful product characteristics



Do not repeat the same fact.



Do NOT use:

- search result titles

- website headings

- manufacturer-number headings

- category navigation

- pricing information

- review information

- unrelated metadata



ATTRIBUTES:



Create technical key-value attributes.



Only include attributes supported by the verified research.



Examples:



"Grit": "50/80/120"

"Backing": "Cloth"

"Pack Quantity": "6"

"Width": "1/2 in"

"Length": "18 in"



APPLICATION:



Use the verified intended application.



INCLUDES:



Describe what is included in the package using verified information.



JSON FORMAT:



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



        if response.startswith("```"):

            response = response.replace(

                "```json",

                "",

            )

            response = response.replace(

                "```",

                "",

            )

            response = response.strip()



        data = json.loads(response)



        if not isinstance(data, dict):

            raise TypeError(

                "Ollama returned a non-object JSON response."

            )



        return data 