from pathlib import Path


def get_html_theme_path():
    return str(Path(__file__).parent.parent)


def setup(app):
    app.add_html_theme("sphinx_kschaul_theme", str(Path(__file__).parent))
    return {"version": "0.1.0", "parallel_read_safe": True}
