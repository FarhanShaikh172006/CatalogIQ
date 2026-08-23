from app.research.web_research import WebResearcher
from app.schemas.product import Product


def test_build_queries() -> None:
    product = Product(
        row_number=2,
        mfg_part_num="DCB518ASTS06G",
        part_desc=(
            "DCB518ASTS06G Diablo "
            "1/2x18 Sanding Belt 6pc"
        ),
        e1_brand="-- Unbranded --",
        unilog_brand="-- No Unilog Brand --",
        dib_brand="-- No DIB Brand --",
        part_manuf="Freud Inc (2435)",
        manufacturer_name="Freud Inc",
        brand_name="Diablo",
        manufacturer_part_number="DCB518ASTS06G",
    )

    researcher = WebResearcher()

    queries = researcher._build_queries(
        product,
    )

    assert len(queries) == 3

    assert '"DCB518ASTS06G"' in queries[0]

    assert "Freud Inc" in queries[0]

    assert "Diablo" in queries[1]