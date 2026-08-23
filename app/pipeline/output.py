from pathlib import Path

import pandas as pd

from app.schemas.enrichment import OllamaEnrichment
from app.schemas.product import Product


# =========================================================
# OUTPUT COLUMNS
# =========================================================

OUTPUT_COLUMNS = [
    "MFR URL",
    "Ref URL 1",
    "Ref URL 2",
    "Ref URL 3",
    "Ref URL 4",
    "Ref URL 5",

    "PART_NUMBER",
    "Dept",
    "Class",
    "Fine",
    "SKU - MY_PART_NUMBER",

    "Mfg_Part_Num",
    "Part_Desc",
    "E1_Brand",
    "Unilog_Brand",
    "DIB_Brand",

    "Part_Manuf",
    "MANUFACTURER_NAME",
    "BRAND_NAME",

    "TRADE_NAME",
    "MANUFACTURER_PART_NUMBER",
    "ALTERNATE_PART_NUMBER",

    "Classpath",

    "MOBILE_DESC",
    "INVOICE_DESC",
    "SHORT_DESC",
    "LONG_DESC1",
    "RETAIL_DESC",
    "MARKETING_DESCRIPTION",
]


# =========================================================
# FEATURES
# =========================================================

OUTPUT_COLUMNS.extend(
    f"ITEM_FEATURES_{index}"
    for index in range(1, 21)
)


# =========================================================
# OTHER PRODUCT INFORMATION
# =========================================================

OUTPUT_COLUMNS.extend(
    [
        "With",
        "Standard/Approvals",
        "Prop 65",
        "Application",
        "Includes",
        "Product Name",
    ]
)


# =========================================================
# ATTRIBUTES
# =========================================================

for index in range(1, 23):
    OUTPUT_COLUMNS.extend(
        [
            f"ATTRIBUTE_LABEL {index}",
            f"ATTRIBUTE_VALUE {index}",
            f"ATTRIBUTE_UOM {index}",
        ]
    )


# =========================================================
# HELPERS
# =========================================================

def _clean(value: object) -> object:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return value


def _get(
    obj: object,
    name: str,
    default: object = "",
) -> object:
    return _clean(
        getattr(
            obj,
            name,
            default,
        )
    )


def _merged_get(
    merged: dict[str, object],
    *names: str,
) -> object:
    """
    Return the first non-empty value from merged data.

    Supports aliases so the output layer remains compatible
    with the research/merger schemas.
    """

    for name in names:
        if name not in merged:
            continue

        value = _clean(
            merged.get(name, "")
        )

        if value == "":
            continue

        if isinstance(value, str) and not value.strip():
            continue

        return value

    return ""


def _set_if_present(
    row: dict[str, object],
    column: str,
    value: object,
) -> None:
    value = _clean(value)

    if value == "":
        return

    if isinstance(value, str) and not value.strip():
        return

    row[column] = value


# =========================================================
# FEATURES
# =========================================================

def _add_features(
    row: dict[str, object],
    features: list[str],
) -> None:

    for index, feature in enumerate(
        features,
        start=1,
    ):
        if index > 20:
            break

        if not feature:
            continue

        cleaned = str(feature).strip()

        if not cleaned:
            continue

        row[
            f"ITEM_FEATURES_{index}"
        ] = cleaned


# =========================================================
# ATTRIBUTES
# =========================================================

def _add_attributes(
    row: dict[str, object],
    attributes: dict[str, str],
) -> None:

    for index, (label, value) in enumerate(
        attributes.items(),
        start=1,
    ):
        if index > 22:
            break

        row[
            f"ATTRIBUTE_LABEL {index}"
        ] = _clean(label)

        row[
            f"ATTRIBUTE_VALUE {index}"
        ] = _clean(value)

        row[
            f"ATTRIBUTE_UOM {index}"
        ] = ""


# =========================================================
# BUILD OUTPUT ROW
# =========================================================

def build_output_row(
    product: Product,
    enrichment: OllamaEnrichment,
    merged: dict[str, object] | None = None,
) -> dict[str, object]:

    if merged is None:
        merged = {}

    row: dict[str, object] = {
        column: ""
        for column in OUTPUT_COLUMNS
    }

    # =====================================================
    # ORIGINAL INPUT DATA
    # =====================================================

    row["Mfg_Part_Num"] = _get(
        product,
        "mfg_part_num",
    )

    row["Part_Desc"] = _get(
        product,
        "part_desc",
    )

    row["E1_Brand"] = _get(
        product,
        "e1_brand",
    )

    row["Unilog_Brand"] = _get(
        product,
        "unilog_brand",
    )

    row["DIB_Brand"] = _get(
        product,
        "dib_brand",
    )

    # =====================================================
    # WEB RESEARCH MAPPING
    # =====================================================

    row["PART_NUMBER"] = _merged_get(
        merged,
        "part_number",
        "manufacturer_part_number",
    )

    row["Dept"] = _merged_get(
        merged,
        "department",
        "dept",
    )

    row["Class"] = _merged_get(
        merged,
        "product_class",
        "class_name",
        "class",
    )

    row["Fine"] = _merged_get(
        merged,
        "fine",
        "product_type",
    )

    row["SKU - MY_PART_NUMBER"] = _merged_get(
        merged,
        "sku",
        "sku_my_part_number",
    )

    row["Part_Manuf"] = _merged_get(
        merged,
        "part_manuf",
        "manufacturer_name",
        "manufacturer",
    )

    row["MANUFACTURER_NAME"] = _merged_get(
        merged,
        "manufacturer_name",
        "manufacturer",
    )

    row["BRAND_NAME"] = _merged_get(
        merged,
        "brand_name",
        "brand",
    )

    row["TRADE_NAME"] = _merged_get(
        merged,
        "trade_name",
        "brand_name",
        "brand",
    )

    row["MANUFACTURER_PART_NUMBER"] = _merged_get(
        merged,
        "manufacturer_part_number",
        "part_number",
    )

    row["ALTERNATE_PART_NUMBER"] = _merged_get(
        merged,
        "alternate_part_number",
    )

    # =====================================================
    # CLASSPATH
    # =====================================================

    classpath = _merged_get(
        merged,
        "classpath",
        "class_path",
    )

    if not classpath:

        department = _merged_get(
            merged,
            "department",
            "dept",
        )

        product_class = _merged_get(
            merged,
            "product_class",
            "class_name",
            "class",
        )

        fine = _merged_get(
            merged,
            "fine",
            "product_type",
        )

        classpath = " > ".join(
            str(value).strip()
            for value in (
                department,
                product_class,
                fine,
            )
            if value
            and str(value).strip()
        )

    row["Classpath"] = classpath

    # =====================================================
    # DESCRIPTIONS
    # =====================================================

    _set_if_present(
        row,
        "MOBILE_DESC",
        enrichment.mobile_description,
    )

    _set_if_present(
        row,
        "INVOICE_DESC",
        enrichment.invoice_description,
    )

    _set_if_present(
        row,
        "SHORT_DESC",
        enrichment.short_description,
    )

    _set_if_present(
        row,
        "LONG_DESC1",
        enrichment.long_description,
    )

    _set_if_present(
        row,
        "RETAIL_DESC",
        enrichment.retail_description,
    )

    _set_if_present(
        row,
        "MARKETING_DESCRIPTION",
        enrichment.marketing_description,
    )

    # =====================================================
    # FEATURES
    # =====================================================

    _add_features(
        row,
        enrichment.features,
    )

    # =====================================================
    # OTHER PRODUCT INFORMATION
    # =====================================================

    _set_if_present(
        row,
        "With",
        getattr(
            enrichment,
            "with_text",
            "",
        ),
    )

    _set_if_present(
        row,
        "Standard/Approvals",
        getattr(
            enrichment,
            "standard_approvals",
            "",
        ),
    )

    _set_if_present(
        row,
        "Prop 65",
        getattr(
            enrichment,
            "prop_65",
            "",
        ),
    )

    _set_if_present(
        row,
        "Application",
        enrichment.application,
    )

    _set_if_present(
        row,
        "Includes",
        enrichment.includes,
    )

    _set_if_present(
        row,
        "Product Name",
        enrichment.product_name,
    )

    # =====================================================
    # ATTRIBUTES
    # =====================================================

    _add_attributes(
        row,
        enrichment.attributes,
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        column: row[column]
        for column in OUTPUT_COLUMNS
    }


# =========================================================
# WRITE EXCEL
# =========================================================

def write_output_excel(
    rows: list[dict[str, object]],
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(
        rows,
        columns=OUTPUT_COLUMNS,
    )

    dataframe = dataframe.fillna("")

    dataframe.to_excel(
        output_path,
        index=False,
    )