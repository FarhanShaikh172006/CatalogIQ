# CatalogIQ

> AI-powered product catalog enrichment and normalization pipeline for structured e-commerce data.

CatalogIQ is an intelligent catalog processing system designed to transform raw manufacturer/product data into enriched, validated, and catalog-ready Excel output. It combines **web research, local AI enrichment, product validation, duplicate detection, persistent caching, and automated Excel generation** into a single processing pipeline.

---

## 🚀 Key Features

* **File Support:** Parses `.csv`, `.xlsx`, and `.xls` catalog formats seamlessly.
* **Web Research Layer:** Searches the web for product/manufacturer data, reference URLs, and official pages.
* **Local AI Integration:** Powered by **Ollama** using the **Qwen3** model for offline-capable, cost-effective structured text generation.
* **Intelligent Caching & Duplication Control:** Bypasses redundant tasks using a persistent product cache and upfront duplicate detection.
* **Validation & Async Jobs:** Validates all enriched items against strict quality criteria and executes pipelines via asynchronous background jobs with live progress tracking.

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │     User / Client   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     FastAPI API     │
                    │   Upload / Status   │
                    │ Cancel / Download   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Catalog Pipeline  │
                    │   Orchestrator      │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌────────────┐    ┌──────────────┐   ┌──────────────┐
      │   Parser   │    │   Duplicate  │   │    Cache     │
      │ CSV / XLSX │    │   Detection  │   │   Lookup     │
      └─────┬──────┘    └──────────────┘   └──────┬───────┘
            │                                      │
            └──────────────────┬───────────────────┘
                               │
                         Cache Miss
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Web Research     │
                    │ Search Provider     │
                    │ Product Verification│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Ollama        │
                    │      Qwen3 LLM      │
                    │ Local AI Enrichment │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Merger         │
                    │ Research + AI +     │
                    │ Original Product    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Validator       │
                    │ Quality Validation  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Excel Exporter    │
                    │   Catalog Output    │
                    └─────────────────────┘

⚙️ Installation & Setup

1. Clone the Repository

git clone [https://github.com/FarhanShaikh172006/CatalogIQ.git](https://github.com/FarhanShaikh172006/CatalogIQ.git)
cd CatalogIQ

2. Create and Activate a Virtual Environment
Windows:

python -m venv .venv
.venv\Scripts\Activate.ps1

macOS / Linux:

python -m venv .venv
source .venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_TIMEOUT=60

🤖 Ollama Setup
Ensure your local Ollama server is running, then pull the required model:

ollama pull qwen3:4b
ollama list
