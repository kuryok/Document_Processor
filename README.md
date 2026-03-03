# Document Preprocessor

Pipeline independente de pré-processamento de documentos para **RAG** (Retrieval-Augmented Generation). Converte PDFs em artefatos estruturados (Markdown, JSONL, JSON) prontos para consumo por qualquer framework downstream — totalmente desacoplado de LangChain, LlamaIndex ou similares.

## Funcionalidades

- **Roteamento Adaptativo por Página** — escolhe automaticamente a melhor estratégia de extração (nativa ou OCR) para cada página
- **Extração Nativa (PyMuPDF)** — texto digital extraído diretamente, sem OCR
- **OCR (PaddleOCR)** — para páginas escaneadas ou com texto insuficiente
- **Fallback em Cascata** — se OCR falhar ou tiver baixa confiança, tenta extração nativa automaticamente
- **Cache Determinístico** — SQLite com chave baseada em hash do conteúdo + parâmetros de extração + versão do pipeline
- **Detecção de Headers/Footers** — identifica por posição Y e similaridade textual entre páginas
- **Estruturação Inteligente** — detecta títulos (H1/H2/H3) por heurísticas de score e listas por prefixo
- **Deduplicação de Blocos** — remove blocos duplicados por hash SHA256 do texto normalizado
- **Schemas Estáveis** — JSONL v1.1 com 15+ campos por bloco, manifest.json e report.json completos

## Saídas Geradas

```
output/{doc_id}/
├── document.md       # Markdown limpo (sem headers/footers)
├── document.jsonl    # Um bloco JSON por linha (schema v1.1)
├── manifest.json     # Metadados do documento e da execução
├── report.json       # Detalhes por página + resumo global
└── pages/            # Imagens PNG das páginas renderizadas
```

## Instalação

```bash
# Clonar e instalar
git clone <repo>
cd Document_Processor
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -e .
```

## Uso

```bash
# Processar um PDF
parse documento.pdf --out ./preprocess/output

# Com config customizada
parse documento.pdf --out ./preprocess/output --config config/quality.yaml

# Modo batch (todos os PDFs de um diretório)
parse ./pasta_entrada/ --out ./preprocess/output --batch

# Só probe (análise rápida sem extração)
parse documento.pdf --out ./preprocess/output --probe-only

# Forçar rota para todas as páginas
parse documento.pdf --out ./preprocess/output --force-route native

# Sem cache
parse documento.pdf --out ./preprocess/output --no-cache

# Logs em texto legível
parse documento.pdf --out ./preprocess/output --log-level DEBUG --log-format text
```

## Configuração

As configurações ficam em `config/default.yaml`. Os principais parâmetros:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `rendering.dpi_default` | 200 | DPI de renderização para OCR |
| `thresholds.native_min_chars` | 30 | Mínimo de caracteres para rota nativa |
| `thresholds.native_min_coverage` | 0.01 | Cobertura mínima de texto na página |
| `thresholds.ocr_confidence_threshold` | 0.75 | Confiança mínima do OCR |
| `cache.enabled` | true | Habilitar cache SQLite |
| `parallelism.parallel_pages` | 2 | Páginas simultâneas no OCR |

## Arquitetura do Pipeline

```
Ingestion → Probe → Extract → Normalize → Structure → Export
   │          │        │          │           │          │
   │          │        │          │           │          ├── document.md
   │          │        │          │           │          ├── document.jsonl
   │          │        │          │           │          ├── manifest.json
   │          │        │          │           │          └── report.json
   │          │        │          │           │
   │          │        │          │           ├── title_detector
   │          │        │          │           ├── list_detector
   │          │        │          │           └── reading_order
   │          │        │          │
   │          │        │          ├── whitespace
   │          │        │          ├── hyphenation
   │          │        │          └── header_footer
   │          │        │
   │          │        ├── NativeExtractor (PyMuPDF)
   │          │        └── OCRAdapter (PaddleOCR)
   │          │
   │          └── analyze_page (heurísticas)
   │
   └── PDFLoader (PyMuPDF, lazy)
```

## Schema JSONL (v1.1)

Cada linha do `document.jsonl` contém um bloco com:

```json
{
  "schema_version": "1.1",
  "doc_id": "sha256:...",
  "source_path": "documento.pdf",
  "page_start": 1,
  "page_end": 1,
  "block_index": 0,
  "block_type": "paragraph",
  "text": "Texto extraído...",
  "markdown": "Texto formatado...",
  "parser_route": "native",
  "language": "pt",
  "bbox": [50.0, 28.5, 500.0, 55.9],
  "hash": "sha256:...",
  "flags": { "is_header": false, "is_footer": false },
  "pipeline_version": "1.1.0",
  "created_at": "2026-01-15T10:23:00Z"
}
```

## Testes

```bash
# Executar testes unitários
python -m pytest tests/unit -v
```

## Roadmap

| Versão | Funcionalidades |
|--------|----------------|
| **v1 (MVP)** ✅ | PDF nativo + OCR, cache, CLI, normalização, estruturação básica |
| **v2** | OCR_VL, Docling, tabelas estruturadas, multi-coluna, DOCX/imagem |
| **v3** | Marker, API REST (FastAPI), fine-tuning de thresholds, PDFs protegidos |

## Dependências Principais

- [PyMuPDF](https://pymupdf.readthedocs.io/) — extração nativa e renderização
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — OCR com GPU
- [Pydantic](https://docs.pydantic.dev/) — modelos de dados
- [Typer](https://typer.tiangolo.com/) — CLI
