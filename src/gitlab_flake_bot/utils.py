from fnmatch import fnmatch

from gitlab import GitlabError


def match_any(filters: list[str], name) -> bool:
    return any(fnmatch(name, f) for f in filters)


def gitlab_try(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except GitlabError:
        return None
