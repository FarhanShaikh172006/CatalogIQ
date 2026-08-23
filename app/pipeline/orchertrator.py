from pathlib import Path
from threading import Event
from typing import Any, Callable

from app.pipeline.cache import ProductCache
from app.pipeline.duplicate_detector import (
    find_duplicates,
    product_key,
)
from app.pipeline.merger import merge_product
from app.pipeline.output import (
    build_output_row,
    write_output_excel,
)
from app.pipeline.parser import parse_catalog
from app.pipeline.validator import validate_product
from app.research.web_research import WebResearcher
from app.services.ollama_enricher import ProductEnricher
from app.schemas.enrichment import OllamaEnrichment


ProgressCallback = Callable[[int, str], None]


class CatalogPipeline:
    """
    End-to-end CatalogIQ catalog processing pipeline.

    Supports:
    - Product parsing
    - Duplicate detection
    - Persistent caching
    - Web research
    - Ollama enrichment
    - Validation
    - Excel export
    - Progress reporting
    - Cancellation
    """

    def __init__(
        self,
        cache_directory: Path | None = None,
        progress_callback: ProgressCallback | None = None,
        cancel_event: Event | None = None,
    ) -> None:
        if cache_directory is None:
            cache_directory = Path(".cache")

        self.cache = ProductCache(cache_directory)
        self.researcher = WebResearcher()
        self.enricher = ProductEnricher()

        self.progress_callback = progress_callback
        self.cancel_event = cancel_event or Event()

    # ============================================================
    # HELPERS
    # ============================================================

    def _check_cancelled(self) -> None:
        """Stop processing if cancellation was requested."""
        if self.cancel_event.is_set():
            raise RuntimeError("Processing cancelled.")

    def _progress(
        self,
        value: int,
        message: str,
    ) -> None:
        """
        Send progress update to the job manager.

        Progress is always clamped between 0 and 100.
        """
        value = max(0, min(100, int(value)))

        if self.progress_callback is not None:
            try:
                self.progress_callback(value, message)
            except Exception:
                # Progress reporting must never kill catalog processing.
                pass

    # ============================================================
    # PROCESS
    # ============================================================

    def process(
        self,
        input_path: Path,
        output_path: Path,
        limit: int | None = None,
    ) -> dict[str, Any]:

        # ========================================================
        # 1. START
        # ========================================================

        self._check_cancelled()

        self._progress(
            1,
            "Starting catalog processing...",
        )

        # ========================================================
        # 2. PARSE CATALOG
        # ========================================================

        self._check_cancelled()

        self._progress(
            5,
            "Reading catalog...",
        )

        products = parse_catalog(input_path)

        if not products:
            raise ValueError(
                "Input catalog contains no products."
            )

        self._check_cancelled()

        self._progress(
            8,
            f"Loaded {len(products)} products.",
        )

        # ========================================================
        # 3. DUPLICATE DETECTION
        # ========================================================

        self._check_cancelled()

        self._progress(
            10,
            "Checking duplicate products...",
        )

        unique_products, duplicates = find_duplicates(products)

        self._check_cancelled()

        # ========================================================
        # 4. APPLY LIMIT
        # ========================================================

        if limit is not None:
            if limit <= 0:
                raise ValueError(
                    "Processing limit must be greater than zero."
                )

            unique_products = unique_products[:limit]

        total_products = len(unique_products)

        if total_products == 0:
            raise ValueError(
                "No unique products to process."
            )

        self._progress(
            12,
            (
                f"Found {total_products} unique products "
                f"to process."
            ),
        )

        # ========================================================
        # COUNTERS
        # ========================================================

        rows: list[dict[str, object]] = []

        validation_errors: list[dict[str, Any]] = []

        cache_hits = 0
        cache_misses = 0
        processed = 0

        # ========================================================
        # PRODUCT PROCESSING
        #
        # Product processing occupies 12% -> 90%.
        # Export occupies 90% -> 100%.
        # ========================================================

        PROCESS_START = 12
        PROCESS_END = 90
        PROCESS_RANGE = PROCESS_END - PROCESS_START

        # ========================================================
        # 5. PROCESS EACH PRODUCT
        # ========================================================

        for index, product in enumerate(
            unique_products,
            start=1,
        ):
            self._check_cancelled()

            # ----------------------------------------------------
            # Calculate product progress
            # ----------------------------------------------------

            product_start = (
                PROCESS_START
                + int(
                    ((index - 1) / total_products)
                    * PROCESS_RANGE
                )
            )

            product_end = (
                PROCESS_START
                + int(
                    (index / total_products)
                    * PROCESS_RANGE
                )
            )

            if product_end <= product_start:
                product_end = product_start + 1

            # ----------------------------------------------------
            # Product started
            # ----------------------------------------------------

            self._progress(
                product_start,
                (
                    f"Processing product "
                    f"{index}/{total_products}..."
                ),
            )

            # ----------------------------------------------------
            # Product key
            # ----------------------------------------------------

            self._check_cancelled()

            key = product_key(product)

            # ----------------------------------------------------
            # Cache lookup
            # ----------------------------------------------------

            self._progress(
                min(product_start + 1, product_end),
                (
                    f"Checking cache "
                    f"{index}/{total_products}..."
                ),
            )

            cached_data = self.cache.get(key)

            # ====================================================
            # CACHE HIT
            # ====================================================

            if cached_data is not None:
                cache_hits += 1

                merged = cached_data

                self._check_cancelled()

                self._progress(
                    min(product_start + 3, product_end),
                    (
                        f"Using cached data "
                        f"{index}/{total_products}..."
                    ),
                )

            # ====================================================
            # CACHE MISS
            # ====================================================

            else:
                cache_misses += 1

                # ------------------------------------------------
                # Web research
                # ------------------------------------------------

                self._check_cancelled()

                self._progress(
                    min(product_start + 3, product_end),
                    (
                        f"Researching product "
                        f"{index}/{total_products}..."
                    ),
                )

                research = self.researcher.research(product)

                self._check_cancelled()

                # ------------------------------------------------
                # Ollama enrichment
                # ------------------------------------------------

                self._progress(
                    min(product_start + 5, product_end),
                    (
                        f"Enriching product with AI "
                        f"{index}/{total_products}..."
                    ),
                )

                enrichment_result = self.enricher.enrich(
                    product,
                    research.model_dump(),
                )

                self._check_cancelled()

                # ------------------------------------------------
                # Merge
                # ------------------------------------------------

                self._progress(
                    min(product_start + 7, product_end),
                    (
                        f"Merging product data "
                        f"{index}/{total_products}..."
                    ),
                )

                merged = merge_product(
                    product,
                    research,
                    enrichment_result,
                )

                self._check_cancelled()

                # ------------------------------------------------
                # Validate
                # ------------------------------------------------

                self._progress(
                    min(product_start + 8, product_end),
                    (
                        f"Validating product "
                        f"{index}/{total_products}..."
                    ),
                )

                errors = validate_product(merged)

                if errors:
                    validation_errors.append(
                        {
                            "row_number": product.row_number,
                            "mfg_part_num": (
                                product.mfg_part_num
                            ),
                            "errors": errors,
                        }
                    )

                    self._progress(
                        product_end,
                        (
                            f"Product {index}/{total_products} "
                            f"completed with validation errors."
                        ),
                    )

                    continue

                # ------------------------------------------------
                # Cache validated result
                # ------------------------------------------------

                self.cache.set(
                    key,
                    merged,
                )

            # ====================================================
            # BUILD ENRICHMENT OBJECT
            # ====================================================

            self._check_cancelled()

            enrichment = OllamaEnrichment(
                product_name=str(
                    merged.get(
                        "product_name",
                        "",
                    )
                ),
                mobile_description=str(
                    merged.get(
                        "mobile_description",
                        "",
                    )
                ),
                invoice_description=str(
                    merged.get(
                        "invoice_description",
                        "",
                    )
                ),
                short_description=str(
                    merged.get(
                        "short_description",
                        "",
                    )
                ),
                long_description=str(
                    merged.get(
                        "long_description",
                        "",
                    )
                ),
                retail_description=str(
                    merged.get(
                        "retail_description",
                        "",
                    )
                ),
                marketing_description=str(
                    merged.get(
                        "marketing_description",
                        "",
                    )
                ),
                features=list(
                    merged.get(
                        "features",
                        [],
                    )
                ),
                application=str(
                    merged.get(
                        "application",
                        "",
                    )
                ),
                includes=str(
                    merged.get(
                        "includes",
                        "",
                    )
                ),
                attributes=dict(
                    merged.get(
                        "attributes",
                        {},
                    )
                ),
            )

            # ====================================================
            # BUILD OUTPUT ROW
            # ====================================================

            self._progress(
                min(product_start + 9, product_end),
                (
                    f"Preparing output "
                    f"{index}/{total_products}..."
                ),
            )

            output_row = build_output_row(
                product,
                enrichment,
                merged,
            )

            # ====================================================
            # MANUFACTURER URL
            # ====================================================

            manufacturer_url = str(
                merged.get(
                    "manufacturer_url",
                    "",
                )
                or ""
            ).strip()

            # ====================================================
            # REFERENCE URLS
            # ====================================================

            reference_urls = merged.get(
                "reference_urls",
                [],
            )

            if not isinstance(
                reference_urls,
                list,
            ):
                reference_urls = []

            reference_urls = [
                str(url).strip()
                for url in reference_urls
                if str(url).strip()
            ]

            # ----------------------------------------------------
            # Remove manufacturer URL from references
            # ----------------------------------------------------

            if manufacturer_url:
                reference_urls = [
                    url
                    for url in reference_urls
                    if url != manufacturer_url
                ]

            # ====================================================
            # WRITE MANUFACTURER URL
            # ====================================================

            output_row["MFR URL"] = manufacturer_url

            # ====================================================
            # WRITE REFERENCE URLS
            # ====================================================

            for url_index, url in enumerate(
                reference_urls,
                start=1,
            ):
                if url_index > 5:
                    break

                output_row[
                    f"Ref URL {url_index}"
                ] = url

            # ====================================================
            # COMPLETED ROW
            # ====================================================

            rows.append(output_row)

            processed += 1

            self._check_cancelled()

            # ====================================================
            # PRODUCT COMPLETE
            # ====================================================

            self._progress(
                product_end,
                (
                    f"Completed product "
                    f"{index}/{total_products}."
                ),
            )

        # ========================================================
        # 6. FINAL CANCELLATION CHECK
        # ========================================================

        self._check_cancelled()

        # ========================================================
        # 7. EXPORT
        # ========================================================

        self._progress(
            92,
            "Preparing enriched Excel catalog...",
        )

        self._check_cancelled()

        self._progress(
            95,
            "Writing enriched Excel catalog...",
        )

        write_output_excel(
            rows,
            output_path,
        )

        self._check_cancelled()

        # ========================================================
        # 8. COMPLETE
        # ========================================================

        self._progress(
            98,
            "Finalizing catalog...",
        )

        self._check_cancelled()

        self._progress(
            100,
            "Catalog processing completed.",
        )

        # ========================================================
        # 9. RETURN STATISTICS
        # ========================================================

        return {
            "input_products": len(products),

            "unique_products": len(
                unique_products
            ),

            "duplicates": sum(
                len(items)
                for items in duplicates.values()
            ),

            "processed": processed,

            "cache_hits": cache_hits,

            "cache_misses": cache_misses,

            "validation_errors": validation_errors,

            "output_path": str(output_path),
        }