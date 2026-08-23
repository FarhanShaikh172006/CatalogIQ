from pydantic import BaseModel, Field


class OllamaEnrichment(BaseModel):
    product_name: str = ""

    category: str = ""

    mobile_description: str = ""

    invoice_description: str = ""

    short_description: str = ""

    long_description: str = ""

    retail_description: str = ""

    marketing_description: str = ""

    features: list[str] = Field(
        default_factory=list,
    )

    with_text: str = ""

    standard_approvals: str = ""

    prop_65: str = ""

    application: str = ""

    includes: str = ""

    attributes: dict[str, str] = Field(
        default_factory=dict,
    )
