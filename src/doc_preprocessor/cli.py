import typer
from pathlib import Path
from typing import Optional
from doc_preprocessor.orchestrator import PipelineOrchestrator
from doc_preprocessor.config.loader import get_default_config, load_config

app = typer.Typer(
    name="doc_preprocessor",
    help="Document Preprocessor CLI para ingestão RAG"
)

@app.command()
def parse(
    input_path: str = typer.Argument(..., help="Caminho para o PDF ou diretório de entrada"),
    out: str = typer.Option(..., "--out", "-o", help="Diretório de saída"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Caminho para config YAML customizado"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Desabilitar cache"),
    probe_only: bool = typer.Option(False, "--probe-only", help="Executar só a fase de Probe (sem Extract)"),
    force_route: Optional[str] = typer.Option(None, "--force-route", help="Forçar rota para todas as páginas (native|ocr)"),
    log_level: str = typer.Option("INFO", "--log-level", help="Nível de log (DEBUG|INFO|WARNING|ERROR)"),
    log_format: str = typer.Option("json", "--log-format", help="Formato de log (json|text)"),
    batch: bool = typer.Option(False, "--batch", help="Modo batch (processa todos os PDFs do diretório)"),
):
    """Processa um documento em artefatos Markdown e JSONL estruturados."""
    input_p = Path(input_path)
    output_p = Path(out)

    if not input_p.exists():
        typer.echo(f"Erro: Caminho não encontrado: {input_p}", err=True)
        raise typer.Exit(1)

    config = get_default_config()
    if config_path:
        config = load_config(config_path)

    # Aplicar overrides de CLI na config
    if no_cache:
        config.cache.enabled = False
    config.logging.level = log_level.upper()
    config.logging.format = log_format.lower()

    orchestrator = PipelineOrchestrator(config)

    # Resolver lista de arquivos
    if input_p.is_dir():
        if not batch:
            typer.echo("Erro: para processar um diretório, use --batch.", err=True)
            raise typer.Exit(1)
        files = list(input_p.glob("*.pdf")) + list(input_p.glob("*.PDF"))
    else:
        files = [input_p]

    if not files:
        typer.echo("Nenhum PDF encontrado no caminho especificado.", err=True)
        raise typer.Exit(1)

    for file_p in files:
        typer.echo(f"Processando {file_p}...")
        try:
            res = orchestrator.run(
                file_p,
                output_p,
                probe_only=probe_only,
                force_route=force_route,
            )
            typer.echo(f"Concluído! Saída em: {res.output_dir}")
        except Exception as e:
            typer.echo(f"Falha ao processar {file_p}: {e}", err=True)


if __name__ == "__main__":
    app()
