from django.apps import AppConfig

from structures import __version__


class StructuresConfig(AppConfig):
    name = "structures"
    label = "structures"
    verbose_name = f"Structures v{__version__}"

    def ready(self) -> None:
        from structures import checks  # noqa: F401 pylint: disable=unused-import
