from app.pipeline.duplicate_detector import (
    find_duplicates,
    product_key,
)
from app.schemas.product import Product


def make_product(
    part_number: str,
    manufacturer: str = "Test Manufacturer",
) -> Product:
    return Product(
        row_number=2,
        mfg_part_num=part_number,
        part_desc="Test Product",
        e1_brand="TestBrand",
        unilog_brand="",
        dib_brand="",
        part_manuf=manufacturer,
        manufacturer_name=manufacturer,
        brand_name="TestBrand",
        manufacturer_part_number=part_number,
    )


def test_same_product_gets_same_key() -> None:
    first = make_product("ABC-123")
    second = make_product("ABC 123")

    assert product_key(first) == product_key(second)


def test_duplicates_are_detected() -> None:
    products = [
        make_product("ABC-123"),
        make_product("ABC-123"),
        make_product("XYZ-999"),
    ]

    unique, duplicates = find_duplicates(products)

    assert len(unique) == 2
    assert len(duplicates) == 1

    duplicate_key = product_key(products[0])

    assert duplicate_key in duplicates
    assert len(duplicates[duplicate_key]) == 1
