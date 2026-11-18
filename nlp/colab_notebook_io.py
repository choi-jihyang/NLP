"""Write source-only, syntax-checked Colab artifacts."""

import ast
import json

from make_colab_notebook import cell


def notebook(path, sections):
    cells = []
    for kind, source in sections:
        if kind == "code":
            ast.parse(source)
        cells.append(cell(kind, source))
    doc = {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"name": path.name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
