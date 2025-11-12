from fnmatch import fnmatch

from gitlab import GitlabError


def match_any(filters: list[str], name) -> bool:
    return any(fnmatch(name, f) for f in filters)


def gitlab_try(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except GitlabError:
        return None


def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg

    return None
