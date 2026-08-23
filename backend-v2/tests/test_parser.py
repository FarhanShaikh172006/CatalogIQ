from pathlib import Path

import pandas as pd

from app.pipeline.parser import parse_catalog


def test_parse_catalog(tmp_path: Path) -> None:
    input_file = tmp_path / "catalog.csv"

    dataframe = pd.DataFrame(
        [
            {
                "Mfg_Part_Num": "TEST-001",
                "Part_Desc": "Test Sanding Belt",
                "E1_Brand": "Diablo",
                "Unilog_Brand": "",
                "DIB_Brand": "",
                "Part_Manuf": "Freud Inc",
            },
            {
                "Mfg_Part_Num": "TEST-002",
                "Part_Desc": "Test Drill Bit",
                "E1_Brand": "DEWALT",
                "Unilog_Brand": "",
                "DIB_Brand": "",
                "Part_Manuf": "Stanley Black & Decker",
            },
        ]
    )

    dataframe.to_csv(input_file, index=False)

    products = parse_catalog(input_file)

    assert len(products) == 2

    assert products[0].mfg_part_num == "TEST-001"
    assert products[0].part_desc == "Test Sanding Belt"

    assert products[1].mfg_part_num == "TEST-002"
    assert products[1].brand_name == "DEWALT"
