import gitlab
from .settings import settings

client: gitlab.Gitlab


def __getattr__(name):
    g = globals()

    if name in g:
        return g[name]

    if name == "client":
        gl = gitlab.Gitlab(settings.gitlab.url, private_token=settings.gitlab.api_token_text)
        gl.auth()

        g[name] = gl

        return gl

    raise AttributeError
