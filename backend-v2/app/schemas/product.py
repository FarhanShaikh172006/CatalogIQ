from pydantic import BaseModel, Field


class Product(BaseModel):
    row_number: int

    mfg_part_num: str = ""
    part_desc: str = ""

    e1_brand: str = ""
    unilog_brand: str = ""
    dib_brand: str = ""

    part_manuf: str = ""

    manufacturer_name: str = ""
    brand_name: str = ""

    manufacturer_part_number: str = ""

    source_row: dict[str, str] = Field(default_factory=dict)
