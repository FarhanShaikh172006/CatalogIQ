import hashlib
import re

from app.schemas.product import Product


def _normalize(value: str) -> str:

    value = value.lower().strip()

    value = re.sub(r"\s+", " ", value)

    value = re.sub(r"[^a-z0-9]+", "", value)

    return value


def product_key(product: Product) -> str:

    manufacturer = _normalize(product.manufacturer_name)

    part_number = _normalize(product.mfg_part_num)

    if manufacturer and part_number:
        identity = f"{manufacturer}:{part_number}"

    elif part_number:
        identity = part_number

    else:
        identity = _normalize(product.part_desc)

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def find_duplicates(
    products: list[Product],
) -> tuple[list[Product], dict[str, list[Product]]]:

    seen: dict[str, Product] = {}
    duplicates: dict[str, list[Product]] = {}

    for product in products:
        key = product_key(product)

        if key not in seen:
            seen[key] = product
            continue

        duplicates.setdefault(key, []).append(product)

    return list(seen.values()), duplicates
