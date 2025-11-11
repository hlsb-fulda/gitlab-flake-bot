import gitlab
from .settings import settings

gl = gitlab.Gitlab(settings.gitlab.url, private_token=settings.gitlab.api_token)
