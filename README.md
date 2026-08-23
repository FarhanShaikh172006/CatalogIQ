# CatalogIQ

## AI-Powered Product Intelligence & Catalog Automation

CatalogIQ is an AI-powered product enrichment and catalog automation platform designed to transform sparse or incomplete product data into **structured, validated, catalog-ready product information**.

It combines **web research, manufacturer and brand resolution, local LLM-based enrichment, product classification, attribute extraction, validation, and automated Excel/CSV generation** into a single pipeline.

The system is designed around the requirements of the **UniHack / UniLog catalog challenge**, where raw product records need to be converted into structured product catalog data.

---

## 🚀 What CatalogIQ Does

CatalogIQ takes an input product dataset containing information such as:

* Manufacturer part number
* Product description
* Existing brand information
* Manufacturer information

and enriches each product using web research and AI.

### Input

Example:

| Field        | Example              |
| ------------ | -------------------- |
| Mfg_Part_Num | DCB518ASTS06         |
| Part_Desc    | 20V MAX battery pack |
| E1_Brand     | DEWALT               |
| Unilog_Brand | DEWALT               |
| DIB_Brand    | DEWALT               |
| Part_Manuf   | DEWALT               |

### Processing

CatalogIQ then performs:

1. Product identification
2. Web research
3. Manufacturer detection
4. Brand resolution
5. Manufacturer URL discovery
6. Part number verification
7. SKU detection
8. Product classification
9. Department classification
10. Product class classification
11. Fine product-type classification
12. Product naming
13. Feature extraction
14. Attribute extraction
15. AI-powered content enrichment
16. Data normalization
17. Validation
18. Output mapping

### Output

The result is a structured catalog containing information such as:

* Manufacturer
* Manufacturer URL
* Brand
* Trade name
* Manufacturer part number
* SKU
* Product name
* Department
* Class
* Fine classification
* Classification path
* Product features
* Product attributes
* Application
* Included items
* Country of origin
* Reference URLs
* AI-generated catalog content
* Validation information

---

# 🧠 Core Idea

Traditional catalog creation requires humans to manually research every product, identify manufacturers, classify products, collect specifications, and format the results.

CatalogIQ automates this workflow.

```text
                RAW PRODUCT DATA
                       │
                       ▼
              ┌─────────────────┐
              │  CSV / Excel    │
              │     Parser      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Product Model   │
              │   & Validation  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Web Research   │
              │     Tavily      │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      Manufacturer            Product
       Resolution             Research
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌─────────────────┐
              │  Ollama / LLM   │
              │    Enrichment   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Classification  │
              │   & Attributes  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Validation    │
              │ & Normalization │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Output Mapping  │
              │ Excel / CSV     │
              └────────┬────────┘
                       │
                       ▼
                CATALOG-READY
                    OUTPUT
```

---

# ✨ Key Features

## 1. Automated Product Research

CatalogIQ uses web search to research products based primarily on:

* Manufacturer part number
* Product description

Queries are automatically generated to locate relevant product pages and technical information.

The current research provider is **Tavily**.

---

## 2. Manufacturer Resolution

The system attempts to identify the actual product manufacturer rather than blindly copying retailer information.

Manufacturer detection considers:

* Existing product manufacturer data
* Brand information
* Search-result metadata
* Product-page content
* Manufacturer phrases
* Official-looking manufacturer domains
* Product titles
* Manufacturer part numbers

Retailer, search-engine, and known aggregator domains are filtered to reduce false manufacturer identification.

---

## 3. Brand Resolution

CatalogIQ can resolve product brands from:

* Existing catalog data
* Web research
* Product metadata
* Manufacturer information

This allows conflicting or incomplete brand information to be normalized.

---

## 4. Manufacturer URL Detection

CatalogIQ attempts to identify the manufacturer's official product domain.

For example:

```text
Product
   ↓
Manufacturer = DEWALT
   ↓
Search results
   ↓
dewalt.com
   ↓
Manufacturer URL
```

Retailers and search engines are excluded from manufacturer URL selection.

---

## 5. Product Classification

Products are automatically classified into a hierarchy:

```text
Department
    ↓
Product Class
    ↓
Fine Product Type
```

Example:

```text
Tools
  └── Power Tools
        └── Drill
```

Another example:

```text
Appliance
  └── Large Appliance
        └── Refrigerator
```

The classification system supports categories such as:

* Appliances
* Electrical
* Plumbing
* HVAC
* Tools
* Hardware
* Safety
* Clothing
* Food

The classification rules can be extended as the catalog grows.

---

# 🤖 AI-Powered Enrichment

CatalogIQ uses an LLM to transform researched product information into structured catalog content.

The project uses **Ollama** as the AI provider.

The current deployment supports the Ollama-compatible model:

```text
gpt-oss:20b
```

The system was designed around a provider abstraction so the AI layer can be changed without rewriting the entire pipeline.

The architecture separates:

```text
Product Research
       │
       ▼
Research Data
       │
       ▼
AI Provider
       │
       ▼
Structured Product Enrichment
```

This keeps web research and AI enrichment independent.

---

# 🌐 Web Research

CatalogIQ currently uses **Tavily** for web search.

The research layer is implemented using:

```text
app/research/
├── search_provider.py
└── web_research.py
```

### Search Provider

`SearchProvider` is responsible only for performing web searches.

It does not perform AI enrichment.

This separation keeps the architecture modular.

### Web Researcher

`WebResearcher` consumes search results and extracts:

* Manufacturer
* Manufacturer URL
* Brand
* Trade name
* Part number
* SKU
* Product name
* Department
* Product class
* Fine classification
* Features
* Attributes
* Application
* Included items
* Country of origin
* Reference URLs
* Source confidence

---

# 🏗️ Architecture

CatalogIQ follows a modular pipeline architecture.

```text
┌─────────────────────────────┐
│        Input Dataset        │
│         CSV / Excel         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           Parser            │
│     Input normalization     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        Product Model        │
│       Pydantic Schema       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Research Pipeline      │
│                             │
│  Tavily → Product Research  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Manufacturer / Brand      │
│        Resolution            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Ollama Enricher       │
│        gpt-oss:20b          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Classification & Attributes │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Validation / Merge      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Output Exporter       │
│       Excel / CSV           │
└─────────────────────────────┘
```

---

# 🛠️ Technology Stack

## Backend

| Technology   | Purpose                           |
| ------------ | --------------------------------- |
| **Python**   | Core programming language         |
| **FastAPI**  | REST API backend                  |
| **Uvicorn**  | ASGI server                       |
| **Pydantic** | Data models and validation        |
| **Pandas**   | Data processing                   |
| **OpenPyXL** | Excel generation and manipulation |
| **Pytest**   | Automated testing                 |

## Artificial Intelligence

| Technology      | Purpose                                              |
| --------------- | ---------------------------------------------------- |
| **Ollama**      | LLM inference provider                               |
| **gpt-oss:20b** | Product enrichment and structured content generation |

## Web Research

| Technology | Purpose                               |
| ---------- | ------------------------------------- |
| **Tavily** | Product and manufacturer web research |

## Frontend

CatalogIQ includes a web frontend for interacting with the processing backend.

The frontend provides the interface for:

* Uploading product datasets
* Starting catalog processing
* Monitoring processing
* Viewing results
* Downloading generated catalog data

## Deployment

The application is designed to run as separate frontend and backend services.

The current deployment uses:

```text
Frontend → Render
Backend  → Render
AI       → Ollama-compatible API
Search   → Tavily API
```

---

# 📁 Project Structure

The backend is organized into independent application layers.

```text
backend-v2/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── agents/
│   │
│   ├── pipeline/
│   │   ├── cache.py
│   │   ├── cache_lookup.py
│   │   ├── duplicate_detector.py
│   │   ├── duplicator.py
│   │   ├── exporter.py
│   │   ├── merger.py
│   │   ├── orchestrator.py
│   │   ├── output.py
│   │   ├── parser.py
│   │   └── validator.py
│   │
│   ├── research/
│   │   ├── search_provider.py
│   │   └── web_research.py
│   │
│   ├── schemas/
│   │   ├── product.py
│   │   ├── research.py
│   │   └── ...
│   │
│   └── services/
│       ├── ollama_enricher.py
│       ├── ollama_provider.py
│       └── ...
│
├── tests/
│   └── test_transform.py
│
├── requirements.txt
├── .env
└── README.md
```

---

# 🔄 Processing Pipeline

The main processing pipeline can be represented as:

```text
Input File
    │
    ▼
Parser
    │
    ▼
Product Objects
    │
    ▼
Duplicate Detection
    │
    ▼
Web Research
    │
    ├── Manufacturer
    ├── Brand
    ├── Part Number
    ├── SKU
    ├── Product URL
    └── Product Information
    │
    ▼
AI Enrichment
    │
    ├── Product Name
    ├── Features
    ├── Attributes
    └── Catalog Content
    │
    ▼
Classification
    │
    ├── Department
    ├── Class
    └── Fine
    │
    ▼
Merge
    │
    ▼
Validation
    │
    ▼
Output Mapping
    │
    ▼
Excel / CSV
```

---

# 📊 UniHack Output Mapping

CatalogIQ is designed to preserve the original input information while adding enriched catalog fields.

The output mapping supports structured catalog sections including:

### Product Identity

* Manufacturer part number
* Manufacturer
* Brand
* Product name
* SKU
* Alternate part number

### Classification

* Department
* Class
* Fine
* Classpath

### Product Content

* Product description
* Product features
* Product attributes
* Application
* Includes

### Source Information

* Manufacturer URL
* Reference URLs
* Source confidence

### Attributes

The output supports multiple:

```text
ATTRIBUTE_LABEL
ATTRIBUTE_VALUE
ATTRIBUTE_UOM
```

groups for structured product specifications.

### Features

The output supports multiple:

```text
ITEM_FEATURE
```

fields for catalog-ready product features.

---

# 🔐 Environment Variables

Create a `.env` file in the backend directory.

Example:

```env
TAVILY_API_KEY=your_tavily_api_key

OLLAMA_BASE_URL=https://your-ollama-endpoint
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_API_KEY=your_ollama_api_key
OLLAMA_TIMEOUT=120
```

Never commit the `.env` file to Git.

The repository should contain:

```gitignore
.env
.venv/
__pycache__/
*.pyc
output/
```

---

# 💻 Local Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd CatalogIQ/backend-v2
```

## 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create:

```text
.env
```

and configure the required Tavily and Ollama settings.

---

# ▶️ Running the Backend

Start FastAPI using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The backend will normally be available at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

---

# 🧪 Running Tests

Run the test suite with:

```bash
pytest -q
```

The project uses Pytest for automated testing of pipeline components.

A successful test run should report passing tests rather than:

```text
collected 0 items
```

because apparently even test frameworks need to be reminded that tests are supposed to exist.

---

# 🧪 Testing Ollama

The AI provider can be tested independently before running the complete catalog pipeline.

Example:

```bash
python test_ollama.py
```

This helps isolate AI-provider problems from:

* CSV parsing
* Web research
* Manufacturer detection
* Catalog merging
* Excel generation

That separation is important when debugging the system.

---

# 📦 Running Catalog Processing

The pipeline can process an input file and generate an output workbook.

Example:

```python
from pathlib import Path

from app.pipeline.orchestrator import CatalogPipeline

pipeline = CatalogPipeline()

pipeline.process(
    Path("Unihack_ Sample Dataset - Input.csv"),
    Path("output/catalog_output.xlsx"),
    limit=7,
)
```

The `limit` parameter is useful during development because it allows a small number of products to be processed before running the entire dataset.

---

# 🔍 Debugging Strategy

CatalogIQ separates the pipeline into multiple components so failures can be isolated.

### If the input fails

Check:

```text
pipeline/parser.py
```

### If web research fails

Check:

```text
research/search_provider.py
research/web_research.py
```

### If manufacturer detection fails

Check:

```text
WebResearcher._find_manufacturer_name()
WebResearcher._find_manufacturer_url()
```

### If AI enrichment fails

Check:

```text
services/ollama_provider.py
services/ollama_enricher.py
```

### If data disappears during processing

Check:

```text
pipeline/merger.py
pipeline/validator.py
```

### If the Excel output is incorrect

Check:

```text
pipeline/exporter.py
pipeline/output.py
```

This modular design makes it possible to debug individual stages without rebuilding the entire system.

---

# 🧩 Design Principles

CatalogIQ follows several important engineering principles.

## Separation of Concerns

Web research, AI enrichment, validation, merging, and exporting are independent components.

```text
Search ≠ AI
AI ≠ Validation
Validation ≠ Export
```

This makes the system easier to maintain and replace.

---

## Provider Abstraction

AI providers are isolated behind provider classes.

This means the catalog pipeline does not need to know the implementation details of the underlying LLM service.

The architecture can therefore support different AI providers without redesigning the entire application.

---

## Structured Output

Instead of relying on free-form AI responses, CatalogIQ expects structured product data.

This allows AI-generated information to pass through validation and mapping before being written to the final catalog.

---

## Deterministic Validation

AI-generated information is not automatically considered correct.

The system uses validation and normalization stages to reduce:

* Missing values
* Invalid classifications
* Duplicate information
* Incorrect formats
* Unwanted source data

---

# ⚡ Performance Considerations

Catalog enrichment requires external operations such as:

* Web search
* AI inference
* Data processing
* Excel generation

For this reason, CatalogIQ supports processing a limited number of products during development.

Example:

```python
limit=7
```

A small test run makes it easier to:

* Identify API failures
* Detect incorrect mappings
* Inspect AI output
* Verify manufacturer detection
* Validate Excel output

before processing a large catalog.

---

# 🔒 Security

API credentials must be stored in environment variables.

Do not commit:

```text
.env
API keys
private credentials
generated secrets
```

The `.gitignore` file should exclude sensitive and generated files.

Example:

```gitignore
.env
.venv/
__pycache__/
*.pyc
output/
```

---

# 🌍 Deployment Architecture

The deployed system is separated into frontend and backend services.

```text
                    USER
                     │
                     ▼
             ┌───────────────┐
             │    Frontend   │
             │    Render     │
             └───────┬───────┘
                     │
                     │ HTTPS API
                     ▼
             ┌───────────────┐
             │    FastAPI    │
             │    Backend    │
             │    Render     │
             └───────┬───────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      ┌───────┐  ┌───────┐  ┌────────┐
      │Tavily │  │Ollama │  │ Output │
      │ Search│  │  LLM  │  │ XLSX   │
      └───────┘  └───────┘  └────────┘
```

This separation allows the frontend and backend to be developed and deployed independently.

---

# 📈 Future Improvements

Potential future improvements include:

* Advanced manufacturer entity resolution
* Better official-domain detection
* More product categories
* Additional retailer filtering
* Improved duplicate detection
* Search-result ranking
* Source verification
* Confidence scoring improvements
* More sophisticated attribute normalization
* UOM normalization
* Automated product image discovery
* Product document and manual discovery
* Batch processing optimization
* Persistent caching
* Background job processing
* Larger-scale catalog processing
* Human review workflows

---

# 🏆 Project Goal

CatalogIQ is designed to demonstrate how modern AI and web-search technologies can automate a traditionally manual catalog-management workflow.

The core objective is:

> **Convert incomplete product data into reliable, structured, catalog-ready product intelligence.**

Instead of requiring a catalog specialist to manually research every product, CatalogIQ combines:

```text
Web Search
     +
Data Processing
     +
AI Enrichment
     +
Classification
     +
Validation
     +
Structured Export
```

into one automated pipeline.

---

# 👨‍💻 Technology Summary

```text
Language
└── Python

Backend
├── FastAPI
├── Uvicorn
└── Pydantic

Data Processing
├── Pandas
└── OpenPyXL

AI
├── Ollama
└── gpt-oss:20b

Web Research
└── Tavily

Testing
└── Pytest

Frontend
└── Web-based catalog processing interface

Deployment
└── Render
```

---

# 📜 Project Status

CatalogIQ currently supports:

* ✅ CSV/Excel product ingestion
* ✅ Product parsing
* ✅ Web research
* ✅ Tavily integration
* ✅ Manufacturer resolution
* ✅ Brand resolution
* ✅ Manufacturer URL discovery
* ✅ Part-number handling
* ✅ SKU extraction
* ✅ Product classification
* ✅ Feature extraction
* ✅ Attribute extraction
* ✅ Ollama-based AI enrichment
* ✅ Structured product schemas
* ✅ Validation
* ✅ Catalog merging
* ✅ Excel output
* ✅ FastAPI backend
* ✅ Web frontend
* ✅ Render deployment
* ✅ Automated testing

---

# 🙌 Conclusion

CatalogIQ combines traditional catalog data processing with modern AI and web research to automate product enrichment at scale.

The architecture is intentionally modular, allowing individual components such as the search provider, AI provider, enrichment logic, validation layer, and output mapper to evolve independently.

The result is a practical pipeline for turning **raw product records into structured, enriched, and catalog-ready product data**.

---

## Built for UniHack / UniLog

**CatalogIQ**
AI-powered product intelligence and catalog automation.
