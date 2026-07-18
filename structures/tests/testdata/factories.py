import datetime as dt
from typing import Generic, List, Optional, TypeVar

import factory
import factory.fuzzy
import yaml
from factory.faker import faker

from django.utils.timezone import now
from eveuniverse.models import EveEntity
from eveuniverse.tests.testdata.factories_2 import (
    EveGroupFactory,
    EveMoonFactory,
    EvePlanetFactory,
    EveSolarSystemFactory,
    EveTypeFactory,
)

from allianceauth.eveonline.models import EveCharacter
from app_utils.testdata_factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
    UserMainFactory,
)

from structures.constants import EveCategoryId, EveGroupId
from structures.core.notification_types import NotificationType
from structures.models import (
    EveSovereigntyMap,
    FuelAlert,
    FuelAlertConfig,
    GeneratedNotification,
    JumpFuelAlertConfig,
    Notification,
    Owner,
    OwnerCharacter,
    PocoDetails,
    StarbaseDetail,
    StarbaseDetailFuel,
    Structure,
    StructureItem,
    StructureService,
    StructureTag,
    Webhook,
)

# from structures.tests.helpers import datetime_to_ldap  # TODO: Use for notifications

T = TypeVar("T")

POSITION_MIN = -100_000_000_000_000_000
POSITION_MAX = 100_000_000_000_000_000

factory.Faker._DEFAULT_LOCALE = "en_US"
_fake = faker.Faker("en_US")


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


# eve universe (within structures)


class PositionFactory(factory.DictFactory, metaclass=BaseMetaFactory[dict]):
    x = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)
    y = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)
    z = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)


class EveEntityFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveEntity]
):
    class Meta:
        model = EveEntity
        django_get_or_create = ("id",)

    category = EveEntity.CATEGORY_CHARACTER

    @factory.lazy_attribute
    def id(self):
        if self.category == EveEntity.CATEGORY_CHARACTER:
            obj = EveCharacterFactory()
            return obj.character_id
        if self.category == EveEntity.CATEGORY_CORPORATION:
            obj = EveCorporationInfoFactory()
            return obj.corporation_id
        if self.category == EveEntity.CATEGORY_ALLIANCE:
            obj = EveAllianceInfoFactory()
            return obj.alliance_id
        raise NotImplementedError(f"Unknown category: {self.category}")


class EveEntityCharacterFactory(EveEntityFactory):
    name = factory.Sequence(lambda n: f"character_name_{n}")
    category = EveEntity.CATEGORY_CHARACTER


class EveEntityCorporationFactory(EveEntityFactory):
    name = factory.Sequence(lambda n: f"corporation_name_{n}")
    category = EveEntity.CATEGORY_CORPORATION


class EveEntityCorporationDEDFactory(EveEntityCorporationFactory):
    id = 1000137
    name = "DED"


class EveEntityAllianceFactory(EveEntityFactory):
    name = factory.Sequence(lambda n: f"alliance_name_{n}")
    category = EveEntity.CATEGORY_ALLIANCE


class EveSolarSystemNullSecFactory(EveSolarSystemFactory):
    security_status = -1.0


class EveSolarSystemLowSecFactory(EveSolarSystemFactory):
    security_status = 0.3


class EveSolarSystemHighSecFactory(EveSolarSystemFactory):
    security_status = 0.9


class EveSolarSystemWSpaceFactory(EveSolarSystemFactory):
    id = factory.Sequence(lambda n: 31_900_000 + n)
    security_status = -1.0


class CitadelServiceModuleTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=66,
        eve_category__name="Service Module",
        id=1321,
        name="Structure Citadel Service Module",
    )


class CitadelTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.STRUCTURE,
        eve_category__name="Structure",
        id=EveGroupId.CITADEL,
        name="Citadel",
    )
    enabled_sections = 1  # Dogmas


class CustomsOfficeTypeFactory(EveTypeFactory):
    id = 2233
    name = "Customs Office"
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.ORBITAL,
        eve_category__name="Orbital",
        id=1025,
        name="Orbital Infrastructure",
    )


class FuelBlockTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=4,
        eve_category__name="Material",
        id=1136,
        name="Fuel Block",
    )


class LiquidOzoneTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=4,
        eve_category__name="Material",
        id=423,
        name="Ice Product",
    )
    id = 16273
    name = "Liquid Ozone"


class IHUBTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=40,
        eve_category__name="Sovereignty Structures",
        id=1012,
        name="Sovereignty Hub",
    )
    id = 32458
    name = "Sovereignty Hub"


class TCUTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=40,
        eve_category__name="Sovereignty Structures",
        id=1003,
        name="Territorial Claim Unit",
    )
    id = 32226
    name = "Territorial Claim Unit"


class PlanetTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=2,
        eve_category__name="Celestial",
        id=7,
        name="Planet",
    )

    @factory.lazy_attribute
    def name(self):
        name = _fake("color")
        return f"Planet ({name.capitalize()})"


class SkyhookTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.ORBITAL,
        eve_category__name="Orbitals",
        id=4736,
        name="Skyhook",
    )
    id = 81080
    name = "Orbital Skyhook"


class MoonDrillTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.STRUCTURE,
        eve_category__name="Structure",
        id=EveGroupId.UPWELL_MOON_DRILL,
        name="Upwell Moon Drill",
    )
    enabled_sections = 1  # Dogmas


class MoonOreTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=25,
        eve_category__name="Asteroid",
        id=1920,
        name="Common Moon Asteroids",
    )


class QuantumCoreTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        id=EveGroupId.QUANTUM_CORES,
        name="Quantum Cores",
    )


class RefineryTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.STRUCTURE,
        eve_category__name="Structure",
        id=EveGroupId.REFINERY,
        name="Refinery",
    )
    enabled_sections = 1  # Dogmas


# Structures objects


class SuperuserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class UserMainBasicFactory(UserMainFactory):
    """Basic user in Structures."""

    main_character__scopes = Owner.esi_scopes()
    permissions__ = ["structures.basic_access"]


class UserMainDefaultFactory(UserMainFactory):
    """Default user in Structures."""

    main_character__scopes = Owner.esi_scopes()
    permissions__ = [
        "structures.basic_access",
        "structures.view_corporation_structures",
    ]


class UserMainDefaultOwnerFactory(UserMainFactory):
    """Default user owning structures."""

    main_character__scopes = Owner.esi_scopes()
    permissions__ = [
        "structures.basic_access",
        "structures.add_structure_owner",
        "structures.view_corporation_structures",
    ]


class FuelAlertConfigFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[FuelAlertConfig]
):
    class Meta:
        model = FuelAlertConfig

    start = 48
    end = 0
    repeat = 12


class FuelAlertFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[FuelAlert]
):
    class Meta:
        model = FuelAlert

    config = factory.SubFactory(FuelAlertConfigFactory)
    hours = 12


class JumpFuelAlertConfigFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[JumpFuelAlertConfig]
):
    class Meta:
        model = JumpFuelAlertConfig

    threshold = 100


class WebhookFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Webhook]
):
    class Meta:
        model = Webhook
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Generated webhook #{n + 1}")
    notes = factory.Faker("sentence")

    @factory.lazy_attribute
    def url(self):
        id = factory.fuzzy.FuzzyInteger(100000000000000000, 999999999999999999).fuzz()
        token = _fake.sha256(raw_output=False)
        return f"https://discord.com/api/webhooks/{id}/{token}"


class OwnerFactory(factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Owner]):
    class Meta:
        model = Owner
        django_get_or_create = ("corporation",)

    class Params:
        user = None  # when specified will use corporation of users's main

    assets_last_update_at = factory.LazyFunction(now)
    character_ownership = None  # no longer used
    forwarding_last_update_at = factory.LazyFunction(now)
    is_alliance_main = False
    is_up = True
    notifications_last_update_at = factory.LazyFunction(now)
    structures_last_update_at = factory.LazyFunction(now)

    @factory.lazy_attribute
    def corporation(self):
        if self.user:
            corporation = self.user.profile.main_character.corporation
            if corporation:
                return corporation
        return EveCorporationInfoFactory()

    @factory.post_generation
    def characters(
        obj, create: bool, extracted: Optional[List[EveCharacter]], **kwargs
    ):
        # Set characters=False to skip creating characters.
        if not create or extracted is False:
            return

        if extracted:
            for eve_character in extracted:
                character_ownership = eve_character.character_ownership
                OwnerCharacterFactory(
                    owner=obj, character_ownership=character_ownership, **kwargs
                )
            return

        # generate new random owner character from this corporation
        OwnerCharacterFactory(owner=obj, **kwargs)

    @factory.post_generation
    def webhooks(self, create, extracted, **kwargs):
        if not create or extracted is False:
            return

        if extracted:
            self.webhooks.add(*extracted)

        else:
            self.webhooks.add(WebhookFactory(**kwargs))


class OwnerCharacterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[OwnerCharacter]
):
    class Meta:
        model = OwnerCharacter

    class Params:
        eve_character = None

    structures_last_used_at = factory.LazyFunction(now)
    notifications_last_used_at = factory.LazyFunction(now)

    @factory.lazy_attribute
    def character_ownership(self):
        if not self.eve_character:
            character = EveCharacterFactory(corporation=self.owner.corporation)
        else:
            character = self.eve_character
        user = UserMainDefaultOwnerFactory(main_character__character=character)
        return user.profile.main_character.character_ownership


class StructureFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Structure]
):
    class Meta:
        model = Structure
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: 1_500_000_000_000 + n)
    eve_type = factory.SubFactory(CitadelTypeFactory)
    eve_solar_system = factory.SubFactory(EveSolarSystemFactory)
    fuel_expires_at = factory.LazyAttribute(lambda obj: now() + dt.timedelta(days=3))
    has_fitting = False
    has_core = True
    last_updated_at = factory.LazyFunction(now)
    name = factory.LazyAttribute(lambda o: f"Test Structure #{o.id}")
    owner = factory.SubFactory(OwnerFactory)
    position_x = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)
    position_y = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)
    position_z = factory.fuzzy.FuzzyFloat(POSITION_MIN, POSITION_MAX)
    state = Structure.State.SHIELD_VULNERABLE

    @factory.post_generation
    def webhooks(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.webhooks.add(*extracted)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.tags.add(*extracted)

    @factory.post_generation
    def quantum_core(obj, create, extracted, **kwargs):
        if not create or extracted is False:
            return

        if obj.eve_type.eve_group_id not in {
            EveGroupId.CITADEL,
            EveGroupId.ENGINEERING_COMPLEX,
            EveGroupId.REFINERY,
        }:
            return

        # add quantum core
        StructureItemFactory(
            structure=obj,
            location_flag=StructureItem.LocationFlag.QUANTUM_CORE_ROOM,
            eve_type=QuantumCoreTypeFactory(),
        )


class RefineryFactory(StructureFactory):
    eve_moon = factory.SubFactory(EveMoonFactory)
    eve_type = factory.SubFactory(RefineryTypeFactory)


class StarbaseTypeFactory(EveTypeFactory):
    eve_group = factory.SubFactory(
        EveGroupFactory,
        eve_category__id=EveCategoryId.STARBASE,
        eve_category__name="Starbase",
        id=EveGroupId.CONTROL_TOWER,
        name="Control Tower",
    )


class StarbaseFactory(StructureFactory):
    eve_type = factory.SubFactory(StarbaseTypeFactory)
    eve_moon = factory.SubFactory(EveMoonFactory)
    has_core = None
    has_fitting = None
    state = Structure.State.POS_ONLINE

    @factory.post_generation
    def starbase_detail(obj, create, extracted, **kwargs):
        if not create or extracted is False:
            return

        StarbaseDetailFactory(structure=obj, **kwargs)


class StarbaseDetailFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[StarbaseDetail]
):
    class Meta:
        model = StarbaseDetail

    structure = factory.SubFactory(StarbaseFactory, starbase_detail=False)

    allow_alliance_members = False
    allow_corporation_members = False
    anchor_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    attack_if_at_war = False
    attack_if_other_security_status_dropping = False
    fuel_bay_take_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    fuel_bay_view_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    last_modified_at = factory.LazyFunction(now)
    offline_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    online_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    unanchor_role = StarbaseDetail.Role.CONFIG_STARBASE_EQUIPMENT_ROLE
    use_alliance_standings = False

    @factory.post_generation
    def fuel_detail(self, create, extracted, **kwargs):
        """Set this param to False to disable."""
        if not create or extracted is False:
            return

        StarbaseDetailFuelFactory(detail=self, quantity=960)


class StarbaseDetailFuelFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[StarbaseDetailFuel]
):
    class Meta:
        model = StarbaseDetailFuel

    eve_type = factory.SubFactory(FuelBlockTypeFactory)
    quantity = 1000


class CustomsOfficeFactory(StructureFactory):
    eve_planet = factory.SubFactory(EvePlanetFactory)
    eve_type = factory.SubFactory(CustomsOfficeTypeFactory)
    has_core = None
    has_fitting = None
    state = Structure.State.NA

    @factory.lazy_attribute
    def name(self):
        return f"Customs Office ({self.eve_planet.name})"

    @factory.post_generation
    def poco_details(self, create, extracted, **kwargs):
        """Set this param to False to disable.

        Set PocoDetails attributes with `poco_details__key=value`
        """
        if not create or extracted is False:
            return

        PocoDetailsFactory(structure=self, **kwargs)


class PocoDetailsFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[PocoDetails]
):
    class Meta:
        model = PocoDetails

    structure = factory.SubFactory(CustomsOfficeFactory, poco_details=False)

    allow_access_with_standings = False
    allow_alliance_access = False
    reinforce_exit_end = 21
    reinforce_exit_start = 18

    standing_level = PocoDetails.StandingLevel.BAD


class SkyhookFactory(StructureFactory):
    has_fitting = None
    has_core = None
    state = Structure.State.NA
    eve_type = factory.SubFactory(SkyhookTypeFactory)
    eve_planet = factory.SubFactory(EvePlanetFactory)
    eve_solar_system = factory.SelfAttribute("eve_planet.eve_solar_system")


class JumpGateFactory(StructureFactory):
    eve_type = factory.SubFactory(
        EveTypeFactory,
        eve_group__id=1408,
        eve_group__name="Upwell Jump Bridge",
        eve_group__eve_category__id=65,
        eve_group__eve_category__name="Structure",
    )

    @factory.post_generation
    def jump_fuel_quantity(self, create, extracted, **kwargs):
        """Set this param to False to disable."""
        if not create or extracted is False:
            return

        StructureItemJumpFuelFactory(
            structure=self,
            quantity=extracted or 1000,  # default
        )


class StructureItemFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[StructureItem]
):
    class Meta:
        model = StructureItem
        django_get_or_create = ("id",)

    id = factory.Sequence(lambda n: 1900000000001 + n)
    is_singleton = False
    location_flag = StructureItem.LocationFlag.CARGO
    quantity = 1
    eve_type = factory.SubFactory(FuelBlockTypeFactory)


class StructureItemJumpFuelFactory(StructureItemFactory):
    is_singleton = False
    location_flag = StructureItem.LocationFlag.STRUCTURE_FUEL
    eve_type = factory.SubFactory(LiquidOzoneTypeFactory)


class StructureServiceFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[StructureService]
):
    class Meta:
        model = StructureService
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Fake Service #{n + 1}")
    state = StructureService.State.ONLINE


class StructureTagFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[StructureTag]
):
    class Meta:
        model = StructureTag
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"name_{n}")
    description = factory.Faker("sentence")


class EveSovereigntyMapFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveSovereigntyMap]
):
    class Meta:
        model = EveSovereigntyMap

    class Params:
        corporation = None

    last_updated = factory.LazyFunction(now)

    @factory.lazy_attribute
    def solar_system_id(self):
        obj = EveSolarSystemFactory(security_status=-1)
        return obj.id

    @factory.lazy_attribute
    def alliance_id(self):
        if self.corporation:
            if self.corporation.alliance:
                return self.corporation.alliance.alliance_id
            raise ValueError("Corporation must be in alliance to have sov")
        return None

    @factory.lazy_attribute
    def corporation_id(self):
        if self.corporation:
            return self.corporation.corporation_id
        return None


class NotificationFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Notification]
):
    class Meta:
        model = Notification

    class Params:
        text_from_dict = None

    notification_id = factory.Sequence(lambda n: 1_500_000_000 + n)
    created = factory.LazyFunction(now)
    is_read = False
    last_updated = factory.LazyAttribute(lambda o: o.created)
    notif_type = NotificationType.WAR_CORPORATION_BECAME_ELIGIBLE
    owner = factory.SubFactory(OwnerFactory)
    sender = factory.SubFactory(EveEntityCorporationFactory, id=1000137, name="DED")
    timestamp = factory.LazyAttribute(lambda o: o.created)

    @factory.lazy_attribute
    def text(self):
        if not self.text_from_dict:
            return ""
        return yaml.dump(self.text_from_dict)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if isinstance(kwargs["notif_type"], NotificationType):
            kwargs["notif_type"] = kwargs["notif_type"].value
        return kwargs


class NotificationMoonMiningExtractionStartedFactory(NotificationFactory):
    class Params:
        auto_time = 132186924601059151
        ready_time = 132186816601059151
        structure = None
        started_by = None

    notif_type = NotificationType.MOONMINING_EXTRACTION_STARTED

    @factory.lazy_attribute
    def text(self):
        started_by = self.started_by or EveEntityCharacterFactory()
        structure = self.structure or RefineryFactory(owner=self.owner)
        ore_1 = MoonOreTypeFactory()
        ore_2 = MoonOreTypeFactory()
        data = {
            "autoTime": self.auto_time,
            "moonID": structure.eve_moon.id,
            "oreVolumeByType": {
                ore_1.id: factory.fuzzy.FuzzyFloat(100_000, 1_000_000).fuzz(),
                ore_2.id: factory.fuzzy.FuzzyFloat(100_000, 1_000_000).fuzz(),
            },
            "readyTime": self.ready_time,
            "solarSystemID": structure.eve_solar_system.id,
            "startedBy": started_by.id,
            "startedByLink": (
                f'<a href="showinfo:1383\\/\\/{started_by.id}">'
                f"{started_by.name}<\\/a>"
            ),
            "structureID": structure.id,
            "structureLink": (
                f'<a href="showinfo:{structure.eve_type.id}\\/\\/'
                f'{structure.id}">{structure.name}<\\/a>'
            ),
            "structureName": structure.name,
            "structureTypeID": structure.eve_type.id,
        }
        return yaml.dump(data)


class NotificationMoonMiningExtractionCanceledFactory(NotificationFactory):
    class Params:
        canceled_by = None
        structure = None

    notif_type = NotificationType.MOONMINING_EXTRACTION_CANCELLED

    @factory.lazy_attribute
    def text(self):
        canceled_by = self.canceled_by or EveEntityCharacterFactory()
        structure = self.structure or RefineryFactory(owner=self.owner)

        data = {
            "cancelledBy": canceled_by.id,
            "cancelledByLink": (
                f'<a href="showinfo:1383\\/\\/{canceled_by.id}">'
                f"{canceled_by.name}<\\/a>"
            ),
            "moonID": structure.eve_moon.id,
            "solarSystemID": structure.eve_solar_system.id,
            "structureID": structure.id,
            "structureLink": (
                f'<a href="showinfo:{structure.eve_type.id}\\/\\/'
                f'{structure.id}">{structure.name}<\\/a>'
            ),
            "structureName": structure.name,
            "structureTypeID": structure.eve_type.id,
        }
        return yaml.dump(data)


class NotificationOrbitalReinforcedFactory(NotificationFactory):
    class Params:
        aggressor_alliance = None
        aggressor_corporation = None
        aggressor_character = None
        structure = None

    notif_type = NotificationType.ORBITAL_REINFORCED

    @factory.lazy_attribute
    def text(self):
        structure = self.structure or CustomsOfficeFactory(owner=self.owner)
        aggressor_alliance = self.aggressor_alliance or EveEntityAllianceFactory()
        aggressor_corporation = (
            self.aggressor_corporation or EveEntityCorporationFactory()
        )
        aggressor_character = self.aggressor_character or EveEntityCharacterFactory()
        data = {
            "aggressorAllianceID": aggressor_alliance.id,
            "aggressorCorpID": aggressor_corporation.id,
            "aggressorID": aggressor_character.id,
            "planetID": structure.eve_planet.id,
            "planetTypeID": structure.eve_planet.eve_type.id,
            "reinforceExitTime": 132154723470000000,  # TODO: make variable
            "solarSystemID": structure.eve_solar_system.id,
            "typeID": structure.eve_type.id,
        }
        return yaml.dump(data)


class NotificationStructureLostShieldFactory(NotificationFactory):
    class Params:
        structure = None

    notif_type = NotificationType.STRUCTURE_LOST_SHIELD

    @factory.lazy_attribute
    def text(self):
        structure = self.structure or StructureFactory(owner=self.owner)
        data = {
            "solarsystemID": structure.eve_solar_system.id,
            "structureID": structure.id,
            "structureShowInfoData": [
                "showinfo",
                structure.eve_type.id,
                structure.id,
            ],
            "structureTypeID": structure.eve_type.id,
            "timeLeft": 1727805401093,
            "timestamp": 132148470780000000,
            "vulnerableTime": 9000000000,
        }
        return yaml.dump(data)


class NotificationSovStructureReinforcedFactory(NotificationFactory):
    class Meta:
        model = Notification
        exclude = ("eve_solar_system", "eve_type")

    class Params:
        campaign_event_type = 1
        decloak_time = 131897990021334067

    notif_type = NotificationType.SOV_STRUCTURE_REINFORCED
    eve_solar_system = factory.SubFactory(EveSolarSystemFactory, security_status=-1)
    eve_type = factory.SubFactory(TCUTypeFactory)

    @factory.lazy_attribute
    def text(self):
        data = {
            "campaignEventType": self.campaign_event_type,
            "decloakTime": self.decloak_time,
            "solarSystemID": self.eve_solar_system.id,
        }
        return yaml.dump(data)


class GeneratedNotificationFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[GeneratedNotification]
):
    class Meta:
        model = GeneratedNotification

    notif_type = NotificationType.TOWER_REINFORCED_EXTRA.value
    owner = factory.SubFactory(OwnerFactory)

    @factory.lazy_attribute
    def details(self):
        reinforced_until = factory.fuzzy.FuzzyDateTime(
            start_dt=now() + dt.timedelta(hours=3),
            end_dt=now() + dt.timedelta(hours=48),
        ).fuzz()
        return {"reinforced_until": reinforced_until.isoformat()}

    @factory.post_generation
    def structures(self, create, extracted, **kwargs):
        if not create or extracted is False:
            return

        if extracted:
            self.structures.add(*extracted)
        else:
            reinforced_until = dt.datetime.fromisoformat(
                self.details["reinforced_until"]
            )
            starbase = StarbaseFactory(
                owner=self.owner,
                state=Structure.State.POS_REINFORCED,
                state_timer_end=reinforced_until,
            )
            self.structures.add(starbase)


class RawNotificationFactory(factory.DictFactory, metaclass=BaseMetaFactory[dict]):
    """Create a raw notification as received from ESI."""

    class Meta:
        exclude = ("data", "timestamp_dt", "sender")

    # excluded
    data = None
    timestamp_dt = None
    sender = factory.SubFactory(EveEntityCorporationFactory, id=2902, name="CONCORD")

    # included
    notification_id = factory.Sequence(lambda o: 1999000000 + o)
    type = "CorpBecameWarEligible"
    sender_id = factory.LazyAttribute(lambda o: o.sender.id)
    sender_type = factory.LazyAttribute(lambda o: o.sender.category)
    is_read = True

    @factory.lazy_attribute
    def timestamp(self):
        if not self.timestamp_dt:
            timestamp_dt = now()
        else:
            timestamp_dt = self.timestamp_dt
        return timestamp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @factory.lazy_attribute
    def text(self):
        if not self.data:
            return ""
        return yaml.dump(self.data)
