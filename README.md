# code2context 🚀

A simple yet powerful CLI tool for packing a project's source code into a single text file, optimized for use as context with Large Language Models (LLMs) like GPT, Claude, Gemini, and more.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What Problem Does It Solve?

When working with LLMs to get help on a software project, we often need to provide the full context of the code: the directory structure, the contents of multiple files, and so on. Manually copying and pasting each file is tedious, error-prone, and messy.

**`code2context`** automates this process. It scans your project, filters out irrelevant files (like binaries, logs, or dependency directories), and generates a single, Markdown-formatted `context.txt` file, ready to be copy-pasted into your favorite LLM.

## ✨ Key Features

*   **🔍 Automatic Exploration:** Traverses your entire project structure to find all files.
*   **⚙️ Smart Filtering:** Uses a `.pathsignore` file (similar to `.gitignore`) to exclude unnecessary files and directories (images, binaries, `node_modules`, etc.).
*   **📝 LLM-Optimized Formatting:** Generates a clean text file with:
    *   A header containing the project name and summary.
    *   A directory tree of the included files.
    *   The content of each file within Markdown code blocks, complete with language identifiers (`python`, `javascript`, etc.).
*   **💻 Easy to Use:** An intuitive command-line interface (CLI) powered by [Typer](https://typer.tiangolo.com/).
*   **📦 Pip Installable:** Easily installed like any other Python package.

## 📦 Installation

You can install `code2context` directly from PyPI (once you publish it):

```bash
pip install code2context
```

## 🚀 Usage

The workflow is a simple two-step process: `explore` and `scan`.

### Step 1: Explore the Project

First, navigate to your project's root directory in your terminal. Then, run the `explore` command. This will find all files and create the initial configuration.

```bash
# Navigate to your project
cd /path/to/your/project

# Run the explore command, using '.' for the current directory
c2c explore .
```

You can also use the `code2context` alias:

```bash
code2context explore .
```

This command will:
1.  Create a hidden directory named `.code2context/` in your project root.
2.  Inside, it will save a list of all found files to `file_paths.txt`.
3.  It will also create a `.pathsignore` file with a default list of exclusion patterns (you can and should edit this).

### Step 2: (Optional) Customize Filtering

Open the newly created `.code2context/.pathsignore` file. You'll see a list of patterns like `.git`, `*.log`, `node_modules`, etc.

You can add or remove patterns here to control exactly which files will be included in the final context. Each pattern should be on a new line.

```text
# .code2context/.pathsignore

# Add patterns to ignore files or directories, one per line.
.git
.vscode
__pycache__
*.log
# Add your own patterns here, for example:
dist/
build/
*.tmp
```

### Step 3: Scan and Generate the Context

Once you are happy with your filter rules, run the `scan` command.

```bash
c2c scan --name "My Awesome App" --summary "This is a web app that manages user tasks using Flask and React."
```

This command will:
1.  Read the list of files.
2.  Filter them using the rules in `.pathsignore`.
3.  Read the content of the remaining files.
4.  Create the `.code2context/context.txt` file with all the formatted content.

The `--name` and `--summary` options are optional but highly recommended to give the LLM better context.

### Step 4: Use the Context

Done! Now you just need to open the `.code2context/context.txt` file, copy its entire contents, and paste it into your chat with an LLM.

## 📄 Example Output (`context.txt`)

Here’s what a generated `context.txt` file might look like for a small project:

````markdown
# Project Context: My Awesome App

## Project Goal

This is a web app that manages user tasks using Flask and React.

## Directory Structure

```
my-awesome-app/
├── .gitignore
├── app.py
└── templates
    └── index.html
```

## File Contents

Below is the content of each relevant text file in the project.

---

### `.gitignore`

```text
__pycache__/
.venv/
```

---

### `app.py`

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    tasks = ["Learn Docker", "Master code2context", "Build something cool"]
    return render_template('index.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)
```

---

### `templates/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>To-Do List</title>
</head>
<body>
    <h1>My Tasks</h1>
    <ul>
        {% for task in tasks %}
        <li>{{ task }}</li>
        {% endfor %}
    </ul>
</body>
</html>
```
````

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features, improvements, or have found a bug, please open an issue on GitHub. If you'd like to contribute code, please fork the repository and submit a pull request.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.