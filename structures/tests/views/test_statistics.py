from django.test import RequestFactory, TestCase

from structures.views import statistics

from ..testdata.factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    OwnerFactory,
    PocoFactory,
    StarbaseFactory,
    StructureFactory,
    UserMainBasicFactory,
    UserMainDefaultFactory,
)
from ..testdata.load_eveuniverse import load_eveuniverse
from .utils import json_response_to_dict


class TestStatistics(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        alliance = EveAllianceInfoFactory(
            alliance_name="Wayne Enterprises", alliance_ticker="WYE"
        )
        cls.corporation = EveCorporationInfoFactory(
            corporation_name="Wayne Technologies", alliance=alliance
        )
        owner = OwnerFactory(corporation=cls.corporation)
        StructureFactory(owner=owner, eve_type_name="Astrahus")
        StructureFactory(owner=owner, eve_type_name="Athanor")
        PocoFactory.create_batch(size=4, owner=owner)
        StarbaseFactory.create_batch(size=3, owner=owner)
        cls.character = EveCharacterFactory(corporation=cls.corporation)

    def test_should_return_summary_data(self):
        # given
        user = UserMainDefaultFactory(main_character__character=self.character)
        # when
        request = self.factory.get("/")
        request.user = user
        response = statistics.structure_summary_data(request)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        obj = data[self.corporation.corporation_id]
        self.assertEqual(obj["corporation_name"], "Wayne Technologies")
        self.assertEqual(obj["alliance_name"], "Wayne Enterprises [WYE]")
        self.assertEqual(obj["citadel_count"], 1)
        self.assertEqual(obj["ec_count"], 0)
        self.assertEqual(obj["refinery_count"], 1)
        self.assertEqual(obj["other_count"], 0)
        self.assertEqual(obj["poco_count"], 4)
        self.assertEqual(obj["starbase_count"], 3)
        self.assertEqual(obj["total"], 9)

    def test_should_return_no_summary_data_without_permission(self):
        # given
        user = UserMainBasicFactory(main_character__character=self.character)
        # when
        request = self.factory.get("/")
        request.user = user
        response = statistics.structure_summary_data(request)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        self.assertFalse(data)
