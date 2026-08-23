from pathlib import Path

from app.pipeline.cache import ProductCache


def test_cache_miss(tmp_path: Path) -> None:
    cache = ProductCache(tmp_path)

    result = cache.get("missing-product")

    assert result is None


def test_cache_write_and_read(tmp_path: Path) -> None:
    cache = ProductCache(tmp_path)

    data = {
        "category": "Sanding Belts",
        "attributes": {
            "Size": "1/2 x 18",
            "Quantity": "6",
        },
    }

    cache.set(
        "product-123",
        data,
    )

    result = cache.get("product-123")

    assert result == data


def test_cache_contains(tmp_path: Path) -> None:
    cache = ProductCache(tmp_path)

    cache.set(
        "product-123",
        {"category": "Sanding Belts"},
    )

    assert cache.contains("product-123")
