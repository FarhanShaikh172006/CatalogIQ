from pydantic import BaseModel, Field


class WebResearchResult(BaseModel):

    manufacturer_url: str = ""

    reference_urls: list[str] = Field(
        default_factory=list
    )

    manufacturer_name: str = ""

    part_manuf: str = ""

    brand_name: str = ""

    trade_name: str = ""

    manufacturer_part_number: str = ""

    alternate_part_number: str = ""

    sku: str = ""

    product_name: str = ""

    department: str = ""

    class_name: str = ""

    product_class: str = ""

    fine: str = ""

    classpath: str = ""

    attributes: dict[str, str] = Field(
        default_factory=dict
    )

    features: list[str] = Field(
        default_factory=list
    )

    application: str = ""

    includes: str = ""

    country_of_origin: str = ""

    source_confidence: float = 0.0