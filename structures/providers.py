"""ESI client provider for Structures."""

from pathlib import Path

from esi.openapi_clients import ESIClientProvider

from . import __version__

spec_file = Path(__file__).parent / "openapi_2025-12-16.json"
esi = ESIClientProvider(
    compatibility_date="2025-12-16",
    ua_appname="aa-structures",
    ua_version=__version__,
    operations=[
        "GetCharactersCharacterIdNotifications",
        "GetCorporationsCorporationIdAssets",
        "GetCorporationsCorporationIdCustomsOffices",
        "GetCorporationsCorporationIdStarbases",
        "GetCorporationsCorporationIdStarbasesStarbaseId",
        "GetCorporationsCorporationIdStructures",
        "GetSovereigntyMap",
        "GetUniverseStructuresStructureId",
        "GetUniverseStructuresStructureId",
        "PostCorporationsCorporationIdAssetsNames",
        "PostCorporationsCorporationIdAssetsLocations",
        "PostCorporationsCorporationIdAssetsNames",
    ],
    spec_file=spec_file,
)
