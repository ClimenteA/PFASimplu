import datetime
from decimal import Decimal

from django.test import TestCase

from utils.decimale import D

from .models import IncasariModel, SursaVenit


class IncasariAlteSurseTest(TestCase):
    def test_totalul_exclude_activitatea_principala(self):
        IncasariModel.objects.create(
            suma=D("100"),
            sursa_venit=SursaVenit.ACTIVITATE_PRINCIPALA.value,
            data_incasarii=datetime.date(2026, 1, 10),
        )
        IncasariModel.objects.create(
            suma=D("50"),
            sursa_venit=SursaVenit.DIVIDENTE_VENIT_DISTRUBUIT.value,
            data_incasarii=datetime.date(2026, 1, 11),
        )
        self.assertEqual(
            IncasariModel.get_total_incasari_alte_surse(2026), Decimal("50")
        )
