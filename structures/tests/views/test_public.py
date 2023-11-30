from django.test import RequestFactory

from app_utils.testing import NoSocketsTestCase

from structures.views import public

from ..testdata.factories import OwnerFactory, PocoFactory, UserMainBasicFactory
from ..testdata.load_eveuniverse import load_eveuniverse
from .utils import json_response_to_dict


class TestPocoListDataView(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        load_eveuniverse()
        cls.user = UserMainBasicFactory()
        cls.main = cls.user.profile.main_character
        owner = OwnerFactory(are_pocos_public=True)
        cls.poco_public = PocoFactory(
            owner=owner,
            eve_planet_name="Amamake V",
            poco_details__allow_access_with_standings=True,
            poco_details__neutral_standing_tax_rate=0.01,
        )
        cls.poco_non_public = PocoFactory()

    def test_should_return_public_pocos_only(self):
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        response = public.public_poco_list_data(request, self.main.character_id)
        # then
        self.assertEqual(response.status_code, 200)
        data = json_response_to_dict(response)
        structure_ids = set(data.keys())
        self.assertSetEqual(structure_ids, {self.poco_public.id})
