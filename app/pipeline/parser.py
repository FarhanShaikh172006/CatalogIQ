from pathlib import Path

import pandas as pd

from app.schemas.product import Product

REQUIRED_COLUMNS = [
    "Mfg_Part_Num",
    "Part_Desc",
    "E1_Brand",
    "Unilog_Brand",
    "DIB_Brand",
    "Part_Manuf",
]


def _clean(value: object) -> str:

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def _validate_columns(dataframe: pd.DataFrame) -> None:

    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]

    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))


def parse_catalog(file_path: Path) -> list[Product]:

    if not file_path.exists():
        raise FileNotFoundError(f"Catalog file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        dataframe = pd.read_csv(file_path)

    elif suffix in {".xlsx", ".xls"}:
        dataframe = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file format. Use CSV, XLSX, or XLS.")

    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    _validate_columns(dataframe)

    products: list[Product] = []

    for index, raw_row in dataframe.iterrows():
        row = {str(column): _clean(value) for column, value in raw_row.items()}

        product = Product(
            row_number=index + 2,
            mfg_part_num=row["Mfg_Part_Num"],
            part_desc=row["Part_Desc"],
            e1_brand=row["E1_Brand"],
            unilog_brand=row["Unilog_Brand"],
            dib_brand=row["DIB_Brand"],
            part_manuf=row["Part_Manuf"],
            manufacturer_name=row["Part_Manuf"],
            brand_name=row["E1_Brand"],
            manufacturer_part_number=row["Mfg_Part_Num"],
            source_row=row,
        )

        products.append(product)

    return products
