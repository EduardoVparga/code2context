import os
import typer

import fnmatch
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated

# --- Configuración ---
CONTEXT_DIR_NAME = ".code2context"
CONTEXT_DIR = Path(CONTEXT_DIR_NAME)
PATHS_FILE = CONTEXT_DIR / "file_paths.txt"
IGNORE_FILE = CONTEXT_DIR / ".pathsignore"
OUTPUT_FILE = CONTEXT_DIR / "context.txt"
PROJECT_ROOT_FILE = CONTEXT_DIR / "project_root.txt"

app = typer.Typer(
    help="Herramienta CLI para empaquetar archivos de texto de un proyecto en un contexto para LLMs."
)

DEFAULT_IGNORE_PATTERNS = [
    "# Añade patrones para ignorar archivos o directorios, uno por línea.",
    ".git", ".vscode", "__pycache__", ".env", "node_modules",
    ".DS_Store", "*.pyc", "*.log", CONTEXT_DIR_NAME,
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg", "*.ico",
    "*.mp3", "*.mp4", "*.avi", "*.mov", "*.flv", "*.wmv",
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
    "*.o", "*.so", "*.a", "*.dll", "*.exe", "*.iso"
]

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.html': 'html',
    '.css': 'css', '.scss': 'scss', '.md': 'markdown', '.json': 'json',
    '.yaml': 'yaml', '.yml': 'yaml', '.sh': 'shell', '.rb': 'ruby',
    '.java': 'java', '.go': 'go', '.rs': 'rust', '.c': 'c', '.cpp': 'cpp',
    '.txt': 'text', '.sql': 'sql', '.php': 'php', '.xml': 'xml'
}

@app.command(help="Explora un directorio y guarda la lista de todos los archivos encontrados.")
def explore(
    path: Annotated[Path, typer.Argument(
        help="La ruta al directorio del proyecto que quieres explorar.",
        exists=True, file_okay=False, readable=True, resolve_path=True,
    )]
):
    typer.echo(f"🔍 Explorando el directorio: {path}")
    typer.echo("🎯 Buscando todos los archivos para su posterior filtrado...")
    CONTEXT_DIR.mkdir(exist_ok=True)
    with open(PROJECT_ROOT_FILE, 'w', encoding="utf-8") as f:
        f.write(str(path))
    all_files = []
    for root, _, files in os.walk(path):
        # Ignorar el propio directorio de contexto
        if CONTEXT_DIR_NAME in Path(root).parts:
            continue
        for name in files:
            file_path = Path(root) / name
            all_files.append(str(file_path.relative_to(path)))

    with open(PATHS_FILE, 'w', encoding="utf-8") as f:
        for file_path in sorted(all_files):
            f.write(f"{file_path}\n")
            
    typer.secho(f"✅ Se encontraron y guardaron {len(all_files)} rutas de archivos en '{PATHS_FILE}'", fg=typer.colors.GREEN)
    
    if not IGNORE_FILE.exists():
        with open(IGNORE_FILE, 'w', encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_IGNORE_PATTERNS))
        typer.echo(f"📄 Se ha creado un archivo de ignorados por defecto en '{IGNORE_FILE}'.")

@app.command(help="Lee, filtra y empaqueta archivos en un 'context.txt' optimizado para LLMs.")
def scan(
    project_name: Annotated[str, typer.Option(
        "--name", "-n", help="El nombre del proyecto para el encabezado."
    )] = "Proyecto sin Nombre",
    summary: Annotated[str, typer.Option(
        "--summary", "-s", help="Un breve resumen del objetivo del proyecto."
    )] = "No se ha proporcionado un resumen del proyecto."
):
    typer.echo("🚀 Iniciando el escaneo optimizado de archivos...")
    required_files = [CONTEXT_DIR, PATHS_FILE, PROJECT_ROOT_FILE]
    if not all(f.exists() for f in required_files):
        typer.secho("Error: Faltan archivos de configuración. Ejecuta 'explore' primero.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with open(PROJECT_ROOT_FILE, 'r', encoding="utf-8") as f:
        project_root = Path(f.read().strip())
    typer.echo(f"📂 Usando la raíz del proyecto: {project_root}")
    
    with open(PATHS_FILE, 'r', encoding="utf-8") as f:
        candidate_files = [line.strip() for line in f.readlines()]

    raw_ignored_patterns = set()
    if IGNORE_FILE.exists():
        with open(IGNORE_FILE, 'r', encoding="utf-8") as f:
            # Normalizamos a forward slashes y quitamos las que estén al final
            raw_ignored_patterns = {
                line.strip().replace("\\", "/").rstrip('/') 
                for line in f if line.strip() and not line.strip().startswith('#')
            }

    included_files_relative = []
    for file_path_str in candidate_files:
        relative_path = Path(file_path_str)
        path_as_posix = relative_path.as_posix()
        
        is_ignored = False
        for pattern in raw_ignored_patterns:
            if fnmatch.fnmatch(relative_path.name, pattern):
                is_ignored = True
                break
            if path_as_posix.startswith(pattern + '/') or path_as_posix == pattern:
                is_ignored = True
                break
        
        if not is_ignored:
            included_files_relative.append(relative_path)
            
    final_context = [
        f"# Contexto del Proyecto: {project_name}\n\n",
        f"## Objetivo del Proyecto\n\n{summary}\n\n",
        "## Estructura de Directorios\n\n",
        f"```\n{generate_directory_tree(project_root.name, included_files_relative)}\n```\n\n",
        "## Contenido de los Archivos\n\n",
        "A continuación se muestra el contenido de cada archivo de texto relevante del proyecto.\n"
    ]

    files_processed = 0
    for relative_path in sorted(included_files_relative):
        absolute_path = project_root / relative_path
        
        if not absolute_path.exists():
            typer.secho(f"❓ Archivo no encontrado (probablemente fue borrado después de 'explore'): {relative_path}", fg=typer.colors.YELLOW)
            continue
        
        try:
            with open(absolute_path, 'r', encoding="utf-8") as f:
                content = f.read()
            
            typer.echo(f"📄 Procesando: {relative_path}")
            lang = LANGUAGE_MAP.get(relative_path.suffix, 'text')
            file_block = ["\n---\n\n", f"### `{relative_path}`\n\n", f"```{lang}\n", content, "\n```\n"]
            final_context.extend(file_block)
            files_processed += 1
        except UnicodeDecodeError:
            typer.secho(f"🙈 Ignorando archivo no-texto (binario): {relative_path}", fg=typer.colors.YELLOW)
        except Exception as e:
            typer.secho(f"❌ Error leyendo el archivo {relative_path}: {e}", fg=typer.colors.RED)

    with open(OUTPUT_FILE, 'w', encoding="utf-8") as f:
        f.write("".join(final_context))
    typer.secho(f"\n✨ ¡Éxito! Se procesaron {files_processed} archivos de texto. Contexto guardado en '{OUTPUT_FILE}'.",
                fg=typer.colors.BRIGHT_GREEN, bold=True)


def generate_directory_tree(project_root_name: str, paths: list[Path]) -> str:
    if not paths:
        return "El proyecto está vacío o todos los archivos fueron ignorados/filtrados."
    tree = {}
    for path in paths:
        current_level = tree
        for part in path.parts:
            current_level = current_level.setdefault(part, {})
    def build_tree_lines(d, prefix=""):
        lines = []
        items = sorted(d.keys())
        for i, name in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if d[name]:
                extension = "    " if i == len(items) - 1 else "│   "
                lines.extend(build_tree_lines(d[name], prefix + extension))
        return lines
    tree_str = f"{project_root_name}/\n"
    tree_str += "\n".join(build_tree_lines(tree))
    return tree_str


if __name__ == "__main__":
    app()