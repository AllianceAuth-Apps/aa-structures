import datetime as dt
from copy import deepcopy
from unittest.mock import patch

from pytz import UTC

from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from structures.constants import EveCorporationId, EveTypeId
from structures.core.notification_types import NotificationType
from structures.models import (
    EveSpaceType,
    JumpFuelAlertConfig,
    PocoDetails,
    Structure,
    StructureItem,
    StructureService,
    StructureTag,
)
from structures.tests.testdata.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveEntityCorporationFactory,
    EveSovereigntyMapFactory,
    FuelAlertConfigFactory,
    JumpGateFactory,
    OwnerFactory,
    PocoDetailsFactory,
    PocoFactory,
    SkyhookFactory,
    StarbaseFactory,
    StructureFactory,
    StructureItemFactory,
    StructureServiceFactory,
    StructureTagFactory,
)
from structures.tests.testdata.load_eveuniverse import load_eveuniverse

STRUCTURES_PATH = "structures.models.structures_1"
NOTIFICATIONS_PATH = "structures.models.notifications"

EVE_ID_HELIUM_FUEL_BLOCK = 4247
EVE_ID_NITROGEN_FUEL_BLOCK = 4051


class TestPocoDetails(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        cls.structure = PocoFactory(owner=cls.owner, poco_details=False)

    def test_should_return_tax_and_access_for_corporation_member(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure, corporation_tax_rate=0.01
        )
        character = EveCharacterFactory(corporation=details.structure.owner.corporation)
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertTrue(result.has_access)
        self.assertTrue(result.is_confident)
        self.assertEqual(result.tax_rate, 0.01)

    def test_should_return_tax_and_access_for_alliance_member(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure, allow_alliance_access=True, alliance_tax_rate=0.02
        )
        corporation = EveCorporationInfoFactory(
            alliance=self.owner.corporation.alliance
        )
        character = EveCharacterFactory(corporation=corporation)
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertTrue(result.has_access)
        self.assertTrue(result.is_confident)
        self.assertEqual(result.tax_rate, 0.02)

    def test_should_return_tax_for_random_1_when_allowed(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure,
            allow_access_with_standings=True,
            standing_level=PocoDetails.StandingLevel.NEUTRAL,
            neutral_standing_tax_rate=0.04,
        )
        character = EveCharacterFactory()
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertTrue(result.has_access)
        self.assertFalse(result.is_confident)
        self.assertEqual(result.tax_rate, 0.04)

    def test_should_return_tax_for_random_2_when_allowed(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure,
            allow_access_with_standings=True,
            standing_level=PocoDetails.StandingLevel.NEUTRAL,
            neutral_standing_tax_rate=0,
        )
        character = EveCharacterFactory()
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertTrue(result.has_access)
        self.assertFalse(result.is_confident)
        self.assertEqual(result.tax_rate, 0)

    def test_should_return_tax_for_random_3_when_allowed(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure,
            allow_access_with_standings=True,
            standing_level=PocoDetails.StandingLevel.TERRIBLE,
            neutral_standing_tax_rate=0.05,
        )
        character = EveCharacterFactory()
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertTrue(result.has_access)
        self.assertFalse(result.is_confident)
        self.assertEqual(result.tax_rate, 0.05)

    def test_should_return_no_access_for_random(self):
        # given
        details = PocoDetailsFactory(
            structure=self.structure, allow_access_with_standings=False
        )
        character = EveCharacterFactory()
        # when
        result = details.determine_access_and_tax_for_character(character)
        # then
        self.assertFalse(result.has_access)
        self.assertFalse(result.is_confident)
        self.assertIsNone(result.tax_rate)

    def test_should_return_standing_map_for_neutral_1(self):
        # given
        details = PocoDetailsFactory(structure=self.structure)
        details.standing_level = PocoDetails.StandingLevel.NEUTRAL
        details.allow_access_with_standings = True
        # when
        result = details.standing_level_access_map()
        # then
        self.assertDictEqual(
            result,
            {
                "NONE": False,
                "TERRIBLE": False,
                "BAD": False,
                "NEUTRAL": True,
                "GOOD": True,
                "EXCELLENT": True,
            },
        )

    def test_should_return_standing_map_for_neutral_2(self):
        # given
        details = PocoDetailsFactory(structure=self.structure)
        details.standing_level = PocoDetails.StandingLevel.NEUTRAL
        details.allow_access_with_standings = False
        # when
        result = details.standing_level_access_map()
        # then
        self.assertDictEqual(
            result,
            {
                "NONE": False,
                "TERRIBLE": False,
                "BAD": False,
                "NEUTRAL": False,
                "GOOD": False,
                "EXCELLENT": False,
            },
        )

    def test_should_return_standing_map_for_terrible(self):
        # given
        details = PocoDetailsFactory(structure=self.structure)
        details.standing_level = PocoDetails.StandingLevel.TERRIBLE
        details.allow_access_with_standings = True
        # when
        result = details.standing_level_access_map()
        # then
        self.assertDictEqual(
            result,
            {
                "NONE": False,
                "TERRIBLE": True,
                "BAD": True,
                "NEUTRAL": True,
                "GOOD": True,
                "EXCELLENT": True,
            },
        )


class TestStructure(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()

    def test_str_upwell(self):
        obj = StructureFactory.build(
            owner=self.owner,
            eve_solar_system_name="Amamake",
            name="Test Structure Alpha",
        )
        expected = "Amamake - Test Structure Alpha"
        self.assertEqual(str(obj), expected)

    def test_str_upwell_wo_solar_system(self):
        obj = StructureFactory.build(
            owner=self.owner,
            eve_solar_system=None,
            name="Test Structure Alpha",
        )
        expected = "? - Test Structure Alpha"
        self.assertEqual(str(obj), expected)

    def test_str_poco(self):
        obj = PocoFactory.build(eve_planet_name="Amamake V")
        expected = "Amamake V - Customs Office (Amamake V)"
        self.assertEqual(str(obj), expected)

    def test_str_starbase(self):
        obj = StarbaseFactory(
            eve_moon_name="Amamake II - Moon 1", name="Home Sweat Home"
        )
        expected = "Amamake II - Moon 1 - Home Sweat Home"
        self.assertEqual(str(obj), expected)

    def test_repr(self):
        obj = StructureFactory.build()
        self.assertTrue(repr(obj))

    def test_structure_is_full_power(self):
        structure = StructureFactory.build(owner=self.owner)

        # true when upwell structure and has fuel that is not expired
        structure.fuel_expires_at = now() + dt.timedelta(hours=1)
        self.assertTrue(structure.is_full_power)

        # false when upwell structure and has fuel, but is expired
        structure.fuel_expires_at = now() - dt.timedelta(hours=1)
        self.assertFalse(structure.is_full_power)

        # False when no fuel info
        structure.fuel_expires_at = None
        self.assertFalse(structure.is_full_power)

        # none when no upwell structure
        poco = PocoFactory(owner=self.owner)
        poco.fuel_expires_at = now() + dt.timedelta(hours=1)
        self.assertIsNone(poco.is_full_power)

    def test_is_low_power(self):
        structure = StructureFactory.build(owner=self.owner)

        # true if Upwell structure and fuel expired and last online < 7d
        structure.fuel_expires_at = now() - dt.timedelta(seconds=3)
        structure.last_online_at = now() - dt.timedelta(days=3)
        self.assertTrue(structure.is_low_power)

        # True if Upwell structure and no fuel info and last online < 7d
        structure.fuel_expires_at = None
        structure.last_online_at = now() - dt.timedelta(days=3)
        self.assertTrue(structure.is_low_power)

        # false if Upwell structure and it has fuel
        structure.fuel_expires_at = now() + dt.timedelta(days=3)
        self.assertFalse(structure.is_low_power)

        # none if upwell structure, but not online info
        structure.fuel_expires_at = now() - dt.timedelta(seconds=3)
        structure.last_online_at = None
        self.assertFalse(structure.is_low_power)

        structure.fuel_expires_at = None
        structure.last_online_at = None
        self.assertFalse(structure.is_low_power)

        # none for non structures
        poco = PocoFactory.build(owner=self.owner)
        self.assertIsNone(poco.is_low_power)

        starbase = StarbaseFactory.build(owner=self.owner)
        self.assertIsNone(starbase.is_low_power)

    def test_is_abandoned(self):
        structure = StructureFactory.build(owner=self.owner)

        # true when upwell structure, online > 7 days
        structure.last_online_at = now() - dt.timedelta(days=7, seconds=1)

        # false when upwell structure, online <= 7 days or none
        structure.last_online_at = now() - dt.timedelta(days=7, seconds=0)
        self.assertFalse(structure.is_abandoned)

        structure.last_online_at = now() - dt.timedelta(days=3)
        self.assertFalse(structure.is_abandoned)

        # none if missing information
        structure.last_online_at = None
        self.assertFalse(structure.is_abandoned)

        # none for non structures
        starbase = StarbaseFactory(owner=self.owner)
        self.assertIsNone(starbase.is_abandoned)

    def test_extract_name_from_esi_response(self):
        expected = "Alpha"
        self.assertEqual(
            Structure.extract_name_from_esi_response("Super - Alpha"), expected
        )
        self.assertEqual(Structure.extract_name_from_esi_response("Alpha"), expected)

    def test_should_return_hours_when_fuel_expires(self):
        # given
        obj = StructureFactory.build(owner=self.owner)
        obj.fuel_expires_at = now() + dt.timedelta(hours=2)
        # when
        result = obj.hours_fuel_expires
        # then
        self.assertAlmostEqual(result, 2.0, delta=0.1)

    def test_should_return_none_when_no_fuel_info(self):
        # given
        obj = StructureFactory.build(owner=self.owner)
        obj.fuel_expires_at = None
        # when
        result = obj.hours_fuel_expires
        # then
        self.assertIsNone(result)

    def test_should_return_moon_location(self):
        # given
        obj = StarbaseFactory.build(eve_moon_name="Amamake II - Moon 1")
        # when/then
        self.assertEqual(obj.location_name, "Amamake II - Moon 1")

    def test_should_return_planet_location(self):
        # given
        obj = PocoFactory.build(eve_planet_name="Amamake V")
        # when/then
        self.assertEqual(obj.location_name, "Amamake V")

    def test_should_return_solar_system_location(self):
        # given
        obj = StructureFactory.build(eve_solar_system_name="Amamake")
        # when/then
        self.assertEqual(obj.location_name, "Amamake")

    def test_should_return_unknown_location(self):
        # given
        obj = StructureFactory.build(eve_solar_system=None)
        # when/then
        self.assertEqual(obj.location_name, "?")

    # TODO: activate
    # def test_is_upwell_structure_data_error(self):
    #     # group without a category
    #     my_group = EveGroup.objects.create(id=299999, name="invalid group")
    #     my_type = EveType.objects.create(
    #         id=199999, name="invalid type", eve_group=my_group
    #     )
    #     self.assertFalse(my_type.is_upwell_structure)

    def test_should_detect_structure_has_position(self):
        # given
        structure = StructureFactory.build(owner=self.owner)
        # then
        self.assertTrue(structure.has_position)

    def test_should_detect_structure_has_no_position(self):
        # given
        structure = StructureFactory.build(
            position_x=None, position_y=None, position_z=None
        )
        # then
        self.assertFalse(structure.has_position)

    def test_should_not_show_structure_as_reinforced(self):
        # given
        structure = StructureFactory(
            owner=self.owner, state=Structure.State.SHIELD_VULNERABLE
        )
        # when/then
        self.assertFalse(structure.is_reinforced)

    def test_should_show_structure_as_reinforced(self):
        structure = StructureFactory.build(owner=self.owner)
        for state, excepted in [
            (Structure.State.ANCHOR_VULNERABLE, False),
            (Structure.State.ANCHORING, False),
            (Structure.State.ARMOR_REINFORCE, True),
            (Structure.State.ARMOR_VULNERABLE, False),
            (Structure.State.DEPLOY_VULNERABLE, False),
            (Structure.State.FITTING_INVULNERABLE, False),
            (Structure.State.HULL_REINFORCE, True),
            (Structure.State.HULL_VULNERABLE, False),
            (Structure.State.ONLINING_VULNERABLE, False),
            (Structure.State.SHIELD_VULNERABLE, False),
            (Structure.State.UNANCHORED, False),
            (Structure.State.NA, False),
            (Structure.State.UNKNOWN, False),
        ]:
            with self.subTest(state=state):
                structure.state = state
                self.assertIs(structure.is_reinforced, excepted)

    def test_should_show_starbase_as_reinforced(self):
        structure = StarbaseFactory.build(owner=self.owner)
        for state, excepted in [
            (Structure.State.POS_OFFLINE, False),
            (Structure.State.POS_ONLINE, False),
            (Structure.State.POS_ONLINING, False),
            (Structure.State.POS_REINFORCED, True),
            (Structure.State.POS_UNANCHORING, False),
        ]:
            with self.subTest(state=state):
                structure.state = state
                self.assertIs(structure.is_reinforced, excepted)

    def test_owner_alliance_has_sov_in_null_sec_system(self):
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        EveSovereigntyMapFactory(
            eve_solar_system_name="1-PGSG", corporation=self.owner.corporation
        )
        self.assertTrue(obj.owner_has_sov())

    def test_owner_has_no_sov_in_null_sec_system(self):
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="A-C5TC")
        self.assertFalse(obj.owner_has_sov())

    def test_owner_has_no_sov_in_low_sec_system(self):
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="Amamake")
        self.assertFalse(obj.owner_has_sov())


class TestStructureIsX(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        cls.jump_gate = JumpGateFactory.build(owner=cls.owner)
        cls.poco = PocoFactory.build(owner=cls.owner)
        cls.skyhook = SkyhookFactory.build(owner=cls.owner)
        cls.starbase = StarbaseFactory.build(owner=cls.owner)
        cls.upwell_structure = StructureFactory.build(owner=cls.owner)

    def test_is_jump_gate(self):
        self.assertFalse(self.upwell_structure.is_jump_gate)
        self.assertFalse(self.poco.is_jump_gate)
        self.assertFalse(self.starbase.is_jump_gate)
        self.assertTrue(self.jump_gate.is_jump_gate)
        self.assertFalse(self.skyhook.is_jump_gate)

    def test_is_poco(self):
        self.assertFalse(self.upwell_structure.is_poco)
        self.assertTrue(self.poco.is_poco)
        self.assertFalse(self.starbase.is_poco)
        self.assertFalse(self.jump_gate.is_poco)
        self.assertFalse(self.skyhook.is_poco)

    def test_is_starbase(self):
        self.assertFalse(self.upwell_structure.is_starbase)
        self.assertFalse(self.poco.is_starbase)
        self.assertTrue(self.starbase.is_starbase)
        self.assertFalse(self.jump_gate.is_starbase)
        self.assertFalse(self.skyhook.is_starbase)

    def test_is_skyhook(self):
        self.assertFalse(self.upwell_structure.is_skyhook)
        self.assertFalse(self.poco.is_skyhook)
        self.assertFalse(self.starbase.is_skyhook)
        self.assertFalse(self.jump_gate.is_skyhook)
        self.assertTrue(self.skyhook.is_skyhook)

    def test_is_upwell_structure(self):
        self.assertTrue(self.upwell_structure.is_upwell_structure)
        self.assertFalse(self.poco.is_upwell_structure)
        self.assertFalse(self.starbase.is_upwell_structure)
        self.assertTrue(self.jump_gate.is_upwell_structure)
        self.assertFalse(self.skyhook.is_upwell_structure)


class TestStructureFuel(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()

    def test_should_return_jump_fuel_quantity(self):
        # given
        structure = JumpGateFactory(owner=self.owner, jump_fuel_quantity=False)
        StructureItemFactory(
            structure=structure,
            eve_type_id=EveTypeId.LIQUID_OZONE,
            location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
            quantity=32,
        )
        StructureItemFactory(
            structure=structure,
            eve_type_id=EveTypeId.LIQUID_OZONE,
            location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
            quantity=10,
        )
        # when
        result = structure.jump_fuel_quantity()
        # then
        self.assertEqual(result, 42)

    def test_should_return_none_when_not_jump_gate_1(self):
        # given
        structure = StarbaseFactory(owner=self.owner, eve_type_name="Astrahus")
        # when
        result = structure.jump_fuel_quantity()
        # then
        self.assertIsNone(result)

    def test_should_return_none_when_not_jump_gate_2(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        # when
        result = structure.jump_fuel_quantity()
        # then
        self.assertIsNone(result)

    def test_should_return_none_when_not_jump_gate_(self):
        # given
        structure = StarbaseFactory(owner=self.owner)
        # when
        result = structure.jump_fuel_quantity()
        # then
        self.assertIsNone(result)

    def test_should_remove_fuel_alerts_when_fuel_level_above_threshold(self):
        # given
        config = JumpFuelAlertConfig.objects.create(threshold=100)
        structure = JumpGateFactory(owner=self.owner, jump_fuel_quantity=101)
        structure.jump_fuel_alerts.create(config=config)
        # when
        structure.reevaluate_jump_fuel_alerts()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 0)

    def test_should_keep_fuel_alerts_when_fuel_level_below_threshold(self):
        # given
        config = JumpFuelAlertConfig.objects.create(threshold=100)
        structure = JumpGateFactory(owner=self.owner, jump_fuel_quantity=99)
        structure.jump_fuel_alerts.create(config=config)
        # when
        structure.reevaluate_jump_fuel_alerts()
        # then
        self.assertEqual(structure.jump_fuel_alerts.count(), 1)

    def test_should_return_fuel_blocks(self):
        # given
        structure = StructureFactory(owner=self.owner)
        StructureItemFactory(
            structure=structure,
            eve_type_id=EVE_ID_NITROGEN_FUEL_BLOCK,
            location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
            quantity=250,
        )
        StructureItemFactory(
            structure=structure,
            eve_type_id=EVE_ID_HELIUM_FUEL_BLOCK,
            location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
            quantity=1000,
        )
        StructureItemFactory(
            structure=structure,
            eve_type_id=EVE_ID_HELIUM_FUEL_BLOCK,
            location_flag=StructureItem.LocationFlag.CARGO,
            quantity=500,
        )
        # when
        result = structure.structure_fuel_quantity
        # then
        self.assertEqual(result, 1250)

    def test_should_return_fuel_need(self):
        # given
        structure = StructureFactory(
            owner=self.owner,
            eve_type_name="Astrahus",
            fuel_expires_at=dt.datetime(2022, 1, 24, 5, 0, tzinfo=UTC),
        )
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 17, 15, 13, tzinfo=UTC)
            StructureItemFactory(
                structure=structure,
                eve_type_id=EVE_ID_NITROGEN_FUEL_BLOCK,
                location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
                quantity=6309,
            )
        # when
        result = structure.structure_fuel_usage()
        # then
        self.assertEqual(result, 168)

    def test_should_not_break_when_no_fuel_date(self):
        # given
        structure = StructureFactory(
            owner=self.owner,
            eve_type_name="Astrahus",
            fuel_expires_at=None,
        )
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = dt.datetime(2021, 12, 17, 15, 13, tzinfo=UTC)
            StructureItemFactory(
                structure=structure,
                eve_type_id=EVE_ID_NITROGEN_FUEL_BLOCK,
                location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
                quantity=6309,
            )
        # when
        result = structure.structure_fuel_usage()
        # then
        self.assertIsNone(result)

    def test_should_handle_zero_hours_remaining(self):
        # given
        my_now = now()
        structure = StructureFactory(
            owner=self.owner,
            eve_type_name="Astrahus",
            fuel_expires_at=my_now,
        )
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = my_now
            StructureItemFactory(
                structure=structure,
                eve_type_id=EVE_ID_NITROGEN_FUEL_BLOCK,
                location_flag=StructureItem.LocationFlag.STRUCTURE_FUEL,
                quantity=1,
                last_updated_at=my_now,
            )
        # when
        result = structure.structure_fuel_usage()
        # then
        self.assertIsNone(result)

    def test_should_return_true_for_structure(self):
        # given
        structure = StructureFactory.build(owner=self.owner)
        # when/then
        self.assertTrue(structure.is_burning_fuel)

    def test_should_return_false_for_structure(self):
        # given
        structure = StructureFactory.build(owner=self.owner, fuel_expires_at=None)
        # when/then
        self.assertFalse(structure.is_burning_fuel)

    def test_should_return_whether_starbase_is_burning_fuel(self):
        starbase = StarbaseFactory.build(owner=self.owner)
        for state, expected in [
            (Structure.State.POS_ONLINE, True),
            (Structure.State.POS_REINFORCED, True),
            (Structure.State.POS_UNANCHORING, True),
            (Structure.State.POS_OFFLINE, False),
            (Structure.State.POS_ONLINING, False),
        ]:
            with self.subTest(state=state):
                starbase.state = state
                self.assertIs(starbase.is_burning_fuel, expected)

    def test_should_return_false_for_poco(self):
        # given
        poco = PocoFactory.build(owner=self.owner)
        # when/then
        self.assertFalse(poco.is_burning_fuel)


@patch(STRUCTURES_PATH + ".STRUCTURES_FEATURE_REFUELED_NOTIFICATIONS", True)
@patch(STRUCTURES_PATH + ".Structure.FUEL_DATES_EQUAL_THRESHOLD_UPWELL", 900)
@patch(STRUCTURES_PATH + ".Structure.FUEL_DATES_EQUAL_THRESHOLD_STARBASE", 7200)
class TestStructureFuelLevels(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory(
            webhooks__notification_types=[NotificationType.STRUCTURE_REFUELED_EXTRA]
        )
        EveEntityCorporationFactory(
            id=EveCorporationId.DED, name="DED"
        )  # for notifications

    @patch(
        NOTIFICATIONS_PATH + ".Notification.send_to_configured_webhooks",
        lambda *args, **kwargs: None,
    )
    def test_should_reset_fuel_notifications_when_refueled_1(self):
        # given
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=12)
        )
        structure.structure_fuel_alerts.create(config=config, hours=12)
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=13)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    @patch(
        NOTIFICATIONS_PATH + ".Notification.send_to_configured_webhooks",
        lambda *args, **kwargs: None,
    )
    def test_should_reset_fuel_notifications_when_fuel_expires_date_has_changed(self):
        # given
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=12)
        )
        old_instance = deepcopy(structure)
        structure.structure_fuel_alerts.create(config=config, hours=12)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=11)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 0)

    @patch(
        NOTIFICATIONS_PATH + ".Notification.send_to_configured_webhooks",
        lambda *args, **kwargs: None,
    )
    def test_should_not_reset_fuel_notifications_when_fuel_expiry_dates_unchanged(self):
        # given
        config = FuelAlertConfigFactory(start=48, end=0, repeat=12)
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=12)
        )
        structure.structure_fuel_alerts.create(config=config, hours=12)
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=12, minutes=5)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertEqual(structure.structure_fuel_alerts.count(), 1)

    @patch(NOTIFICATIONS_PATH + ".Notification.create_from_structure")
    def test_should_generate_structure_refueled_notif_when_fuel_level_increased(
        self, mock_create_from_structure
    ):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=6)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertTrue(mock_create_from_structure.called)
        _, kwargs = mock_create_from_structure.call_args
        self.assertEqual(
            kwargs["notif_type"], NotificationType.STRUCTURE_REFUELED_EXTRA
        )

    @patch(NOTIFICATIONS_PATH + ".Notification.create_from_structure")
    def test_should_generate_tower_refueled_notif_when_fuel_level_increased(
        self, mock_create_from_structure
    ):
        # given
        structure = StarbaseFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=4)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertTrue(mock_create_from_structure.called)
        _, kwargs = mock_create_from_structure.call_args
        self.assertEqual(kwargs["notif_type"], NotificationType.TOWER_REFUELED_EXTRA)

    @patch(NOTIFICATIONS_PATH + ".Notification.send_to_webhook")
    def test_should_generate_refueled_notif_when_fuel_level_increased(
        self, mock_send_to_webhook
    ):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=12)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertTrue(mock_send_to_webhook.called)

    @patch(NOTIFICATIONS_PATH + ".Notification.send_to_webhook")
    def test_should_not_generate_refueled_notif_when_fuel_level_almost_unchanged(
        self, mock_send_to_webhook
    ):
        # given
        target_date_1 = now() + dt.timedelta(hours=2)
        target_date_1 = now() + dt.timedelta(hours=2, minutes=15)  # FIXME
        structure = StructureFactory(owner=self.owner, fuel_expires_at=target_date_1)
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = target_date_1
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertFalse(mock_send_to_webhook.called)

    @patch(NOTIFICATIONS_PATH + ".Notification.send_to_webhook")
    def test_should_not_generate_refueled_notif_fuel_level_decreased(
        self, mock_send_to_webhook
    ):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=12)
        )
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = now() + dt.timedelta(hours=1)
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertFalse(mock_send_to_webhook.called)

    @patch(NOTIFICATIONS_PATH + ".Notification.send_to_webhook")
    def test_should_not_generate_refueled_notif_fuel_is_removed(
        self, mock_send_to_webhook
    ):
        # given
        structure = StructureFactory(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=2)
        )
        old_instance = deepcopy(structure)
        # when
        structure.fuel_expires_at = None
        structure.handle_fuel_notifications(old_instance)
        # then
        self.assertFalse(mock_send_to_webhook.called)


class TestStructurePowerMode(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()

    def test_returns_none_for_non_upwell_structures(self):
        starbase = StarbaseFactory.build(owner=self.owner)
        self.assertIsNone(starbase.power_mode)

        pos = PocoFactory.build(owner=self.owner)
        self.assertIsNone(pos.power_mode)

        structure = StructureFactory.build(owner=self.owner)
        self.assertIsNotNone(structure.power_mode)

    def test_full_power_mode(self):
        structure = StructureFactory.build(
            owner=self.owner, fuel_expires_at=now() + dt.timedelta(hours=1)
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.FULL_POWER)
        self.assertEqual(structure.get_power_mode_display(), "Full Power")

    def test_low_power_mode_1(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=now() - dt.timedelta(seconds=3),
            last_online_at=now() - dt.timedelta(days=3),
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.LOW_POWER)

    def test_low_power_mode_2(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=None,
            state=Structure.State.ANCHORING,
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.LOW_POWER)

    def test_low_power_mode_3(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=now() - dt.timedelta(days=3),
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.LOW_POWER)
        self.assertEqual(structure.get_power_mode_display(), "Low Power")

    def test_abandoned_mode_1(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=now() - dt.timedelta(seconds=3),
            last_online_at=now() - dt.timedelta(days=7, seconds=1),
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.ABANDONED)

    def test_abandoned_mode_2(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=now() - dt.timedelta(days=7, seconds=1),
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.ABANDONED)
        self.assertEqual(structure.get_power_mode_display(), "Abandoned")

    def test_low_abandoned_mode_1(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=now() - dt.timedelta(seconds=3),
            last_online_at=None,
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.LOW_ABANDONED)

    def test_low_abandoned_mode_2(self):
        structure = StructureFactory.build(
            owner=self.owner,
            fuel_expires_at=None,
            last_online_at=None,
        )
        self.assertEqual(structure.power_mode, Structure.PowerMode.LOW_ABANDONED)
        self.assertEqual(structure.get_power_mode_display(), "Abandoned?")


class TestStructureTags(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        EveSovereigntyMapFactory(
            eve_solar_system_name="1-PGSG", corporation=cls.owner.corporation
        )

    def test_can_create_generated_tags(self):
        # given
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        obj.tags.clear()
        # when
        obj.update_generated_tags()
        # then
        null_tag = StructureTag.objects.get(name=StructureTag.NAME_NULLSEC_TAG)
        self.assertIn(null_tag, list(obj.tags.all()))
        sov_tag = StructureTag.objects.get(name=StructureTag.NAME_SOV_TAG)
        self.assertIn(sov_tag, list(obj.tags.all()))

    def test_can_update_generated_tags(self):
        # given
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        null_tag = StructureTag.objects.get(name=StructureTag.NAME_NULLSEC_TAG)
        self.assertIn(null_tag, list(obj.tags.all()))
        null_tag.order = 100
        null_tag.style = StructureTag.Style.DARK_BLUE
        null_tag.save()

        sov_tag = StructureTag.objects.get(name=StructureTag.NAME_SOV_TAG)
        self.assertIn(sov_tag, list(obj.tags.all()))
        sov_tag.order = 100
        sov_tag.style = StructureTag.Style.RED
        sov_tag.save()

        # when
        obj.update_generated_tags(recreate_tags=True)

        # then
        null_tag.refresh_from_db()
        self.assertEqual(null_tag.style, StructureTag.Style.RED)
        self.assertEqual(null_tag.order, 50)
        sov_tag.refresh_from_db()
        self.assertEqual(sov_tag.style, StructureTag.Style.DARK_BLUE)
        self.assertEqual(sov_tag.order, 20)

    def test_can_handle_unknown_space_type_for_existing_tags(self):
        # given
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        obj.tags.clear()
        # when
        with patch(
            "structures.models.eveuniverse.EveSpaceType.from_solar_system"
        ) as mock:
            mock.return_value = EveSpaceType.UNKNOWN
            obj.update_generated_tags()

        # then
        self.assertEqual(obj.tags.count(), 1)
        sov_tag = StructureTag.objects.get(name=StructureTag.NAME_SOV_TAG)
        self.assertIn(sov_tag, list(obj.tags.all()))

    def test_can_handle_unknown_space_type_when_recreating_tags(self):
        # given
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        obj.tags.clear()
        # when
        with patch(
            "structures.models.eveuniverse.EveSpaceType.from_solar_system"
        ) as mock:
            mock.return_value = EveSpaceType.UNKNOWN
            obj.update_generated_tags(recreate_tags=True)

        # then
        self.assertEqual(obj.tags.count(), 1)
        sov_tag = StructureTag.objects.get(name=StructureTag.NAME_SOV_TAG)
        self.assertIn(sov_tag, list(obj.tags.all()))


class TestStructureTag(NoSocketsTestCase):
    def test_str(self):
        obj = StructureTag(name="Super cool tag")
        self.assertEqual(str(obj), "Super cool tag")

    def test_repr(self):
        obj = StructureTag.objects.create(name="Super cool tag")
        expected = "StructureTag(name='Super cool tag')"
        self.assertEqual(repr(obj), expected)

    def test_list_sorted(self):
        x1 = StructureTag(name="Alpha")
        x2 = StructureTag(name="charlie")
        x3 = StructureTag(name="bravo")
        tags = [x1, x2, x3]

        self.assertListEqual(StructureTag.sorted(tags), [x1, x3, x2])
        self.assertListEqual(StructureTag.sorted(tags, reverse=True), [x2, x3, x1])

    def test_html_default(self):
        x = StructureTag(name="Super cool tag")
        self.assertEqual(
            x.html, '<span class="label label-default">Super cool tag</span>'
        )

    def test_html_primary(self):
        x = StructureTag(name="Super cool tag", style="primary")
        self.assertEqual(
            x.html, '<span class="label label-primary">Super cool tag</span>'
        )


class TestStructureSave(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        cls.owner = OwnerFactory()
        EveSovereigntyMapFactory(
            eve_solar_system_name="1-PGSG", corporation=cls.owner.corporation
        )

    def test_can_save_tags_low_sec(self):
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="Amamake")
        lowsec_tag = StructureTag.objects.get(name=StructureTag.NAME_LOWSEC_TAG)
        self.assertIn(lowsec_tag, obj.tags.all())
        self.assertIsNone(
            StructureTag.objects.filter(name=StructureTag.NAME_SOV_TAG).first()
        )

    def test_can_save_tags_null_sec_w_sov(self):
        obj = StructureFactory(owner=self.owner, eve_solar_system_name="1-PGSG")
        nullsec_tag = StructureTag.objects.get(name=StructureTag.NAME_NULLSEC_TAG)
        self.assertIn(nullsec_tag, obj.tags.all())
        sov_tag = StructureTag.objects.get(name=StructureTag.NAME_SOV_TAG)
        self.assertIn(sov_tag, obj.tags.all())

    def test_should_create_default_tags(self):
        # given
        default_tag = StructureTagFactory(is_default=True)
        # when
        obj = StructureFactory(owner=self.owner)
        # then
        self.assertIn(default_tag, obj.tags.all())

    def test_should_not_create_default_tags(self):
        # given
        default_tag = StructureTagFactory(is_default=True)
        # when
        obj = StructureFactory(owner=self.owner)
        obj.tags.all().delete()
        obj.save()
        # then
        self.assertNotIn(default_tag, obj.tags.all())


class TestStructureNoSetup(NoSocketsTestCase):
    def test_structure_get_matching_state(self):
        self.assertEqual(
            Structure.State.from_esi_name("anchoring"),
            Structure.State.ANCHORING,
        )
        self.assertEqual(
            Structure.State.from_esi_name("not matching name"),
            Structure.State.UNKNOWN,
        )

    def test_structure_service_get_matching_state(self):
        self.assertEqual(
            StructureService.State.from_esi_name("online"),
            StructureService.State.ONLINE,
        )
        self.assertEqual(
            StructureService.State.from_esi_name("offline"),
            StructureService.State.OFFLINE,
        )
        self.assertEqual(
            StructureService.State.from_esi_name("not matching"),
            StructureService.State.OFFLINE,
        )


class TestStructureService(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    def test_str(self):
        structure = StructureFactory(
            eve_solar_system_name="Amamake", name="Test Structure Alpha"
        )
        obj = StructureServiceFactory(structure=structure, name="Clone Bay")
        expected = "Amamake - Test Structure Alpha - Clone Bay"
        self.assertEqual(str(obj), expected)
