from dataclasses import dataclass
from typing import Any

from app.pipeline.cache import ProductCache
from app.pipeline.duplicate_detector import product_key
from app.schemas.product import Product


@dataclass
class CacheResult:
    product: Product