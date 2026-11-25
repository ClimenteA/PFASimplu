"""Tool-urile MCP expuse pentru PFASimplu.

Atentie: aici NU exista tool-uri de stergere (drop data, delete etc.).
Operatiile distructive raman doar in interfata web.
"""

from __future__ import annotations

import base64
import binascii
from contextlib import contextmanager
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from .auth import current_key_user_id
from .django_setup import setup_django

setup_django()

from cheltuieli.forms import CheltuieliForm
from cheltuieli.models import CheltuialaModel
from core.settings import APP_VERSION
from documente.models import DocumenteModel
from facturi.models import FacturaModel
from incasari.forms import IncasariForm
from incasari.models import IncasariModel
from setari.models import SetariModel
from utils.calcule import calculeaza_taxe_si_impozite
from utils.decimale import D, rotund2
from utils.multiuser import _current_user


@contextmanager
def user_context():
    """Ruleaza tool-ul in contextul contului care a generat cheia MCP.

    Astfel managerii Django (UserScopedManager) filtreaza automat datele si
    fisierele: agentul vede si modifica doar ce apartine acelui cont.
    """
    user_id = current_key_user_id()
    if user_id is None:
        raise ValueError(
            "Cheia MCP nu are cont asociat. Genereaza o cheie noua in /setari."
        )
    user = get_user_model().objects.filter(pk=user_id).first()
    if user is None:
        raise ValueError(
            "Contul asociat cheii MCP nu mai exista. Genereaza o cheie noua in /setari."
        )
    token = _current_user.set(user)
    try:
        yield user
    finally:
        _current_user.reset(token)


def _ban(value: Any) -> str:
    """Sumele se intorc ca string, ca sa nu piarda zecimalele prin JSON."""
    return str(rotund2(D(value or 0)))


def _fisier(fisier_base64: str | None, nume_fisier: str | None) -> ContentFile:
    """Construieste fisierul cerut de formular.

    Agentul poate trimite continutul (base64) al documentului justificativ.
    Daca nu il trimite, se creaza un fisier-text scurt, ca sa nu blocam
    inregistrarea (campul `fisier` e obligatoriu in model).
    """
    if fisier_base64:
        try:
            continut = base64.b64decode(fisier_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"Continutul base64 nu este valid: {exc}") from exc
        if not continut:
            raise ValueError("Fisierul trimis este gol.")
        nume = nume_fisier or "document_mcp.pdf"
        return ContentFile(continut, name=nume)

    nume = (nume_fisier or "document_mcp.txt").rsplit(".", 1)[0] + ".txt"
    return ContentFile(
        "Document justificativ inregistrat prin serverul MCP PFASimplu.\n",
        name=nume,
    )


def _erores(form) -> str:
    return " ".join(
        f"{camp}: {', '.join(mesaje)}" for camp, mesaje in form.errors.items()
    )


def register_tools(mcp) -> None:
    """Inregistreaza tool-urile pe o instanta FastMCP."""

    @mcp.tool
    def ping() -> dict:
        """Verifica conexiunea si intoarce versiunea aplicatiei."""
        return {
            "status": "ok",
            "aplicatie": "PFASimplu MCP",
            "versiune": APP_VERSION,
            "tooluri": "readonly + add_incasare/add_cheltuiala (fara stergere)",
        }

    @mcp.tool
    def get_setari() -> dict:
        """Intoarce datele PFA din pagina Setari (nume, CIF, IBAN, scutiri etc.)."""
        with user_context():
            s = SetariModel.objects.first()
            if s is None:
                return {"exista": False}
            return {
                "exista": True,
                "nume": s.nume,
                "cif": s.cif,
                "nr_reg_com": s.nr_reg_com,
                "localitate": s.localitate,
                "adresa": s.adresa,
                "email": s.email,
                "telefon": s.telefon,
                "conturi_iban": [
                    {"valuta": c.valuta, "iban": c.iban} for c in s.conturi.all()
                ],
                "caen_principal": s.caen_principal,
                "caen_secondare": s.caen_secondare or [],
                "cod_tva_intracomunitar": s.cod_tva_intracomunitar,
                "cont_iban_trezoreria": s.cont_iban_trezoreria,
                "scutit_cas": bool(s.scutit_cas),
                "scutit_cass": bool(s.scutit_cass),
                "scutit_impozit": bool(s.scutit_impozit),
            }

    @mcp.tool
    def list_incasari(
        an: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Listeaza incasarile, optional filtrate pe an."""
        with user_context():
            qs = IncasariModel.objects.all().order_by("-data_inserarii", "-id")
            if an:
                qs = qs.filter(data_inserarii__year=an)
            return [
                {
                    "id": i.id,
                    "data": i.data_inserarii.isoformat() if i.data_inserarii else None,
                    "sursa_venit": i.sursa_venit,
                    "suma": str(i.suma),
                    "suma_in_ron": _ban(i.suma_in_ron),
                    "valuta": i.valuta,
                    "tip_tranzactie": i.tip_tranzactie,
                    "fisier": i.fisier.name if i.fisier else None,
                }
                for i in qs[: max(1, min(limit, 500))]
            ]

    @mcp.tool
    def list_cheltuieli(
        an: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Listeaza cheltuielile, optional filtrate pe an."""
        with user_context():
            qs = CheltuialaModel.objects.all().order_by("-data_inserarii", "-id")
            if an:
                qs = qs.filter(data_inserarii__year=an)
            return [
                {
                    "id": c.id,
                    "data": c.data_inserarii.isoformat() if c.data_inserarii else None,
                    "nume": c.nume_cheltuiala,
                    "suma": str(c.suma),
                    "suma_in_ron": _ban(c.suma_in_ron),
                    "valuta": c.valuta,
                    "deductibila": c.deductibila,
                    "tip_achizitie": c.tip_achizitie,
                    "mijloc_fix": bool(c.mijloc_fix),
                    "fisier": c.fisier.name if c.fisier else None,
                }
                for c in qs[: max(1, min(limit, 500))]
            ]

    @mcp.tool
    def list_facturi(
        an: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Listeaza facturile emise, optional filtrate pe an."""
        with user_context():
            qs = FacturaModel.objects.all().order_by("-data_emitere", "-id")
            if an:
                qs = qs.filter(data_emitere__year=an)
            return [
                {
                    "id": f.id,
                    "serie_numar": f"{f.serie}-{f.numar}",
                    "data_emitere": f.data_emitere.isoformat()
                    if f.data_emitere
                    else None,
                    "client": f.nume,
                    "cif": f.cif,
                    "total_de_plata": _ban(f.total_de_plata),
                    "valuta": f.valuta,
                    "tip_factura": f.tip_factura,
                }
                for f in qs[: max(1, min(limit, 500))]
            ]

    @mcp.tool
    def list_documente(
        an: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Listeaza documentele urcate, optional filtrate pe an."""
        with user_context():
            qs = DocumenteModel.objects.all().order_by("-actualizat_la", "-id")
            if an:
                qs = qs.filter(data_document__year=an)
            return [
                {
                    "id": d.id,
                    "tip_document": d.tip_document,
                    "document_pentru_anul": d.document_pentru_anul,
                    "mentiuni": d.mentiuni,
                    "fisier": d.fisier.name if d.fisier else None,
                }
                for d in qs[: max(1, min(limit, 500))]
            ]

    @mcp.tool
    def sumar_an(an: int) -> dict:
        """Totaluri incasari/cheltuieli, venit net, taxe estimate si TVA autolichidata."""
        with user_context():
            brut = IncasariModel.get_total_incasari(an)
            cheltuieli = CheltuialaModel.get_total_cheltuieli(an)
            net = rotund2(D(brut) - D(cheltuieli))
            setari = SetariModel.objects.first()
            taxe = calculeaza_taxe_si_impozite(
                max(net, D(0)),
                an,
                bool(setari and setari.scutit_cas),
                bool(setari and setari.scutit_cass),
                bool(setari and setari.scutit_impozit),
            )
            rezultat = {
                "an": an,
                "total_incasari_brut": _ban(brut),
                "total_cheltuieli": _ban(cheltuieli),
                "venit_net": _ban(net),
                "taxe_si_impozite_estimate": {k: _ban(v) for k, v in taxe.items()},
                "facturi_neincasate": _ban(IncasariModel.get_total_neincasate(an)),
            }
            try:
                from utils.tva import calculeaza_jurnal_cumparari

                jurnal = calculeaza_jurnal_cumparari(an)
                if jurnal:
                    rezultat["tva_autolichidata_d301"] = _ban(jurnal["total_tva"])
            except Exception:
                # Jurnalul de cumparari e optional (depinde de codul de TVA).
                pass
            return rezultat

    @mcp.tool
    def add_incasare(
        suma: str,
        data: str,
        sursa_venit: str = "Venit din activitati independente",
        valuta: str = "RON",
        tip_tranzactie: str = "BANCAR",
        fisier_base64: str | None = None,
        nume_fisier: str | None = None,
    ) -> dict:
        """Adauga o incasare. `data` e YYYY-MM-DD; `fisier_base64` e documentul optional."""
        with user_context():
            form = IncasariForm(
                {
                    "suma": suma,
                    "data_inserarii": data,
                    "sursa_venit": sursa_venit,
                    "valuta": valuta,
                    "tip_tranzactie": tip_tranzactie,
                },
                files={"fisier": _fisier(fisier_base64, nume_fisier)},
            )
            if not form.is_valid():
                raise ValueError(f"Datele incasarii nu sunt valide: {_erores(form)}")
            obj = form.save()
            return {
                "id": obj.id,
                "suma_in_ron": _ban(obj.suma_in_ron),
                "data": obj.data_inserarii.isoformat() if obj.data_inserarii else None,
                "fisier": obj.fisier.name,
            }

    @mcp.tool
    def add_cheltuiala(
        nume_cheltuiala: str,
        suma: str,
        data: str,
        deductibila: str = "Deductibila integral",
        valuta: str = "RON",
        tip_tranzactie: str = "BANCAR",
        tip_achizitie: str = "Romania",
        fisier_base64: str | None = None,
        nume_fisier: str | None = None,
    ) -> dict:
        """Adauga o cheltuiala. `data` e YYYY-MM-DD; nu este expusa nicio operatie de stergere."""
        with user_context():
            form = CheltuieliForm(
                {
                    "nume_cheltuiala": nume_cheltuiala,
                    "suma": suma,
                    "data_inserarii": data,
                    "deductibila": deductibila,
                    "valuta": valuta,
                    "tip_tranzactie": tip_tranzactie,
                    "tip_achizitie": tip_achizitie,
                },
                files={"fisier": _fisier(fisier_base64, nume_fisier)},
            )
            if not form.is_valid():
                raise ValueError(f"Datele cheltuielii nu sunt valide: {_erores(form)}")
            obj = form.save()
            return {
                "id": obj.id,
                "nume": obj.nume_cheltuiala,
                "suma_in_ron": _ban(obj.suma_in_ron),
                "data": obj.data_inserarii.isoformat() if obj.data_inserarii else None,
                "deducere_in_ron": _ban(obj.deducere_in_ron),
                "tva_autolichidata": _ban(obj.tva_autolichidata),
                "fisier": obj.fisier.name,
            }
