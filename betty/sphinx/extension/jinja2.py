from sphinx.application import Sphinx


def render_jinja2(app: Sphinx, docname: str, source: list[str]) -> None:
    """
    Handle Sphinx's source-read event to render source code as Jinja2 templates.
    """
    if app.builder.format != 'html':
        return

    source[0] = app.builder.templates.render_string(
        source[0], app.config.html_context
    )


def setup(app: Sphinx) -> None:
    """
    Implement Sphinx's extension setup.
    """
    app.connect('source-read', render_jinja2)
