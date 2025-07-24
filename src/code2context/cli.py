import os
import typer
import fnmatch
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated

# --- Configuration ---
CONTEXT_DIR_NAME = ".code2context"
CONTEXT_DIR = Path(CONTEXT_DIR_NAME)
PATHS_FILE = CONTEXT_DIR / "file_paths.txt"
IGNORE_FILE = CONTEXT_DIR / ".pathsignore"
OUTPUT_FILE = CONTEXT_DIR / "context.txt"
PROJECT_ROOT_FILE = CONTEXT_DIR / "project_root.txt"

app = typer.Typer(
    help="CLI tool to package text files from a project into a context for LLMs."
)

DEFAULT_IGNORE_PATTERNS = [
    "# Add patterns to ignore files or directories, one per line.",
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

@app.command(help="Explore a directory and save the list of all found files.")
def explore(
    path: Annotated[Path, typer.Argument(
        help="The path to the project directory you want to explore.",
        exists=True, file_okay=False, readable=True, resolve_path=True,
    )]
):
    typer.echo(f"🔍 Exploring directory: {path}")
    typer.echo("🎯 Finding all files for later filtering...")
    CONTEXT_DIR.mkdir(exist_ok=True)
    with open(PROJECT_ROOT_FILE, 'w', encoding="utf-8") as f:
        f.write(str(path))
    all_files = []
    for root, _, files in os.walk(path):
        # Ignore the context directory itself
        if CONTEXT_DIR_NAME in Path(root).parts:
            continue
        for name in files:
            file_path = Path(root) / name
            all_files.append(str(file_path.relative_to(path)))

    with open(PATHS_FILE, 'w', encoding="utf-8") as f:
        for file_path in sorted(all_files):
            f.write(f"{file_path}\n")
            
    typer.secho(f"✅ Found and saved {len(all_files)} file paths in '{PATHS_FILE}'", fg=typer.colors.GREEN)
    
    if not IGNORE_FILE.exists():
        with open(IGNORE_FILE, 'w', encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_IGNORE_PATTERNS))
        typer.echo(f"📄 A default ignore file has been created at '{IGNORE_FILE}'.")

@app.command(help="Read, filter, and package files into a 'context.txt' optimized for LLMs.")
def scan(
    project_name: Annotated[str, typer.Option(
        "--name", "-n", help="The name of the project for the header."
    )] = "Unnamed Project",
    summary: Annotated[str, typer.Option(
        "--summary", "-s", help="A brief summary of the project's goal."
    )] = "No project summary provided."
):
    typer.echo("🚀 Starting optimized file scan...")
    required_files = [CONTEXT_DIR, PATHS_FILE, PROJECT_ROOT_FILE]
    if not all(f.exists() for f in required_files):
        typer.secho("Error: Configuration files are missing. Run 'explore' first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with open(PROJECT_ROOT_FILE, 'r', encoding="utf-8") as f:
        project_root = Path(f.read().strip())
    typer.echo(f"📂 Using project root: {project_root}")
    
    with open(PATHS_FILE, 'r', encoding="utf-8") as f:
        candidate_files = [line.strip() for line in f.readlines()]

    raw_ignored_patterns = set()
    if IGNORE_FILE.exists():
        with open(IGNORE_FILE, 'r', encoding="utf-8") as f:
            # Normalize to forward slashes and remove any trailing slashes
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
        f"# Project Context: {project_name}\n\n",
        f"## Project Goal\n\n{summary}\n\n",
        "## Directory Structure\n\n",
        f"```\n{generate_directory_tree(project_root.name, included_files_relative)}\n```\n\n",
        "## File Contents\n\n",
        "The content of each relevant text file in the project is shown below.\n"
    ]

    files_processed = 0
    for relative_path in sorted(included_files_relative):
        absolute_path = project_root / relative_path
        
        if not absolute_path.exists():
            typer.secho(f"❓ File not found (it was likely deleted after 'explore'): {relative_path}", fg=typer.colors.YELLOW)
            continue
        
        try:
            with open(absolute_path, 'r', encoding="utf-8") as f:
                content = f.read()
            
            typer.echo(f"📄 Processing: {relative_path}")
            lang = LANGUAGE_MAP.get(relative_path.suffix, 'text')
            file_block = ["\n---\n\n", f"### `{relative_path}`\n\n", f"```{lang}\n", content, "\n```\n"]
            final_context.extend(file_block)
            files_processed += 1
        except UnicodeDecodeError:
            typer.secho(f"🙈 Ignoring non-text (binary) file: {relative_path}", fg=typer.colors.YELLOW)
        except Exception as e:
            typer.secho(f"❌ Error reading file {relative_path}: {e}", fg=typer.colors.RED)

    with open(OUTPUT_FILE, 'w', encoding="utf-8") as f:
        f.write("".join(final_context))
    typer.secho(f"\n✨ Success! Processed {files_processed} text files. Context saved to '{OUTPUT_FILE}'.",
                fg=typer.colors.BRIGHT_GREEN, bold=True)


def generate_directory_tree(project_root_name: str, paths: list[Path]) -> str:
    if not paths:
        return "The project is empty or all files were ignored/filtered."
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