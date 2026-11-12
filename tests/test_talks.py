# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the talks helpers with made-up data. Run: python -m unittest discover -s tests
import importlib.util
import pathlib
import unittest
from datetime import date, timedelta

_FILE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components" / "cvv_dashboard" / "talks.py"
)
_SPEC = importlib.util.spec_from_file_location("cvv_talks", _FILE)
talks = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(talks)

OGGI = date(2026, 10, 21)


def _voce(giorni, ora="09:00", docente="Docente A", stato="disponibile"):
    return {
        "data": (OGGI + timedelta(days=giorni)).isoformat(),
        "ora_inizio": ora, "docente": docente, "stato": stato,
    }


class RangeTests(unittest.TestCase):
    def test_range_is_28_days(self):
        primo, ultimo = talks.intervallo(OGGI)
        self.assertEqual(primo, OGGI)
        self.assertEqual((ultimo - primo).days, 27)

    def test_filter_edges(self):
        voci = [_voce(-1), _voce(0), _voce(27), _voce(28)]
        giorni = [v["data"] for v in talks.filtra_ordina(voci, OGGI)]
        self.assertEqual(giorni, [_voce(0)["data"], _voce(27)["data"]])

    def test_range_moves_after_midnight(self):
        voci = [_voce(0), _voce(28)]
        domani = OGGI + timedelta(days=1)
        giorni = [v["data"] for v in talks.filtra_ordina(voci, domani)]
        self.assertEqual(giorni, [_voce(28)["data"]])

    def test_request_date_format(self):
        self.assertEqual(talks.formato_richiesta(OGGI), "20261021")

    def test_sort_by_date_then_time(self):
        voci = [_voce(2, "10:00"), _voce(1, "11:00"), _voce(1, "09:00")]
        ordinate = talks.filtra_ordina(voci, OGGI)
        self.assertEqual(
            [(v["data"], v["ora_inizio"]) for v in ordinate],
            [(_voce(1)["data"], "09:00"), (_voce(1)["data"], "11:00"), (_voce(2)["data"], "10:00")],
        )

    def test_empty_list(self):
        self.assertEqual(talks.filtra_ordina([], OGGI), [])
        self.assertEqual(talks.unisci(None, None), [])


class MergeTests(unittest.TestCase):
    SLOT = {"frames": [
        {"id": 1, "teacherName": "Docente A", "date": "2026-10-22", "startTime": "09:00"},
        {"id": 2, "teacherName": "Docente B", "date": "2026-10-23", "startTime": "10:00"},
    ]}

    def test_valid_booked_row_has_safe_details(self):
        prenotati = {"talks": [
            {"id": 1, "teacherName": "Docente A", "date": "2026-10-22", "startTime": "09:00",
             "room": "Aula 3", "url": "https://example.org/m"},
        ]}
        voci = talks.unisci(self.SLOT, prenotati)
        self.assertEqual(len(voci), 3)
        self.assertEqual([v["stato"] for v in voci], ["disponibile", "disponibile", "prenotato"])
        booked = voci[2]
        self.assertEqual(booked["data"], "2026-10-22")
        self.assertEqual(booked["docente"], "Docente A")
        self.assertEqual(booked["dati"], "")

    def test_unknown_booked_row_stays_booked(self):
        voci = talks.unisci(self.SLOT, [{"talkDate": "2026-10-24", "altro": 1}])
        self.assertEqual(len(voci), 3)
        self.assertEqual(voci[2]["stato"], "prenotato")

    def test_mixed_booked_rows_all_count(self):
        prenotati = [{"date": "2026-10-22"}, {"talkDate": "x"}, "testo", None, {}]
        voci = talks.unisci(self.SLOT, prenotati)
        self.assertEqual([v["stato"] for v in voci].count("prenotato"), 5)
        self.assertEqual([v["stato"] for v in voci].count("disponibile"), 2)

    def test_empty_booked_response_means_no_booked_rows(self):
        for vuoto in (None, [], {}, {"talks": []}):
            voci = talks.unisci(self.SLOT, vuoto)
            self.assertEqual([v["stato"] for v in voci], ["disponibile", "disponibile"])

    def test_malformed_slot_row_is_not_a_booked_flag(self):
        with self.assertRaises(talks.RispostaNonRiconosciuta):
            talks.unisci({"frames": [{"teacherName": "X"}]}, [{"a": 1}])

    def test_booked_rows_without_date_are_kept_and_last(self):
        voci = talks.unisci(self.SLOT, [{"x": 1}])
        ordinate = talks.filtra_ordina(voci, date(2026, 10, 21))
        self.assertEqual(len(ordinate), 3)
        self.assertEqual(ordinate[-1]["stato"], "prenotato")

    def test_describe_has_no_values(self):
        testo = talks.descrivi([{"talkDate": "2026-10-24", "nome": "Segreto"}, {"id": 3}])
        self.assertIn("righe=2", testo)
        self.assertIn("talkDate:str", testo)
        self.assertIn("id:int", testo)
        self.assertNotIn("2026", testo)
        self.assertNotIn("Segreto", testo)

    def test_missing_fields_stay_empty(self):
        voci = talks.unisci({"frames": [{"date": "2026-10-22"}]}, None)
        self.assertEqual(voci[0]["docente"], "")
        self.assertEqual(voci[0]["link"], "")

    def test_entry_without_date_raises(self):
        with self.assertRaises(talks.RispostaNonRiconosciuta):
            talks.unisci({"frames": [{"teacherName": "X"}]}, None)

    def test_unknown_body_raises(self):
        with self.assertRaises(talks.RispostaNonRiconosciuta):
            talks.unisci({"Qualcosa": "altro"}, None)

    def test_empty_valid_body_is_empty(self):
        self.assertEqual(talks.unisci({"Teacher": [], "Talks": []}, []), [])


class NestedTests(unittest.TestCase):
    CORPO = {
        "Teacher": [
            {
                "TeacherName": "Docente A",
                "Subjects": ["Materia X", {"SubjectDesc": "Materia Y"}],
                "Frames": [
                    {
                        "FrameDate": "2026-10-22", "FrameTimeFrom": "09:00", "FrameTimeTo": "09:30",
                        "FramePlace": "Aula 2",
                        "FreeSlotTimeRange": ["09:00 - 09:10", "09:10 - 09:20", "09:20 - 09:30"],
                    },
                ],
            },
            {
                "TeacherName": "Docente B",
                "Subjects": [],
                "Frames": [{"FrameDate": "2026-10-23", "FrameTimeFrom": "15:00", "FrameTimeTo": "15:10"}],
            },
        ],
        "Talks": [],
    }

    def test_free_slots_without_bookings(self):
        voci = talks.unisci(self.CORPO, [])
        self.assertEqual(len(voci), 4)
        self.assertTrue(all(v["stato"] == "disponibile" for v in voci))
        self.assertEqual([v["ora_inizio"] for v in voci], ["09:00", "09:10", "09:20", "15:00"])
        self.assertEqual(voci[0]["ora_fine"], "09:10")
        self.assertEqual(voci[0]["docente"], "Docente A")
        self.assertEqual(voci[0]["materia"], "Materia X, Materia Y")
        self.assertEqual(voci[0]["aula"], "Aula 2")
        self.assertEqual(voci[3]["materia"], "")

    def test_booked_rows_do_not_change_the_slots(self):
        voci = talks.unisci(self.CORPO, [{"teacherName": "Docente A", "date": "2026-10-22"}])
        self.assertEqual(len(voci), 5)
        self.assertEqual([v["stato"] for v in voci][:4], ["disponibile"] * 4)
        self.assertEqual(voci[4]["stato"], "prenotato")

    def test_nested_items_sort_by_date_and_time(self):
        voci = talks.filtra_ordina(talks.unisci(self.CORPO, None), date(2026, 10, 21))
        self.assertEqual([v["data"] for v in voci][-1], "2026-10-23")
        self.assertEqual(voci[0]["ora_inizio"], "09:00")

    def test_teacher_without_known_fields_raises(self):
        with self.assertRaises(talks.RispostaNonRiconosciuta):
            talks.unisci({"Teacher": [{"TeacherName": "X", "Frames": [{"Altro": 1}]}]}, None)


def _prenotato(giorni=1, **extra):
    riga = {
        "talkDate": (OGGI + timedelta(days=giorni)).isoformat(), "startHour": "09:00",
        "endHour": "09:10", "teacherId": 11, "teacherName": "Docente A", "place": "Aula 4",
        "flagByDist": False, "talkId": 100 + giorni, "live_link": None,
    }
    riga.update(extra)
    return riga


# nested shape of teachersframes2 is not confirmed: made-up rows with the reported field names
SLOT_ID = {"teachers": [
    {"teacherId": 11, "teacherName": "Docente A", "subjects": ["Materia X", {"subjectDesc": "Materia Y"}],
     "frames": []},
    {"teacherId": 11, "teacherName": "Docente A", "subjects": ["Materia X", "Materia Z"], "frames": []},
    {"teacherId": 12, "teacherName": "Docente B", "subjects": [], "frames": []},
]}

PRIVATI = {
    "cellNumber": "SEGRETO-1", "emailAddr": "SEGRETO-2", "otherContact": "SEGRETO-3",
    "bookedBy": "SEGRETO-4", "live_pw": "SEGRETO-5", "message": "SEGRETO-6",
    "myMsg": "SEGRETO-7", "teacherMsg": "SEGRETO-8",
}


class ModeTests(unittest.TestCase):
    def test_boolean_flag(self):
        self.assertEqual(talks._modo({"flagByDist": True}), "distanza")
        self.assertEqual(talks._modo({"flagByDist": False}), "presenza")

    def test_missing_null_and_unknown_are_unknown(self):
        for voce in ({}, {"flagByDist": None}, {"flagByDist": "boh"}, {"mode": 7},
                     {"flagByDist": "false"}, {"flagByDist": 1}):
            self.assertEqual(talks._modo(voce), "", voce)

    def test_text_whitespace_and_case(self):
        for testo in ("distanza", " A Distanza ", "REMOTE", "Remoto", "distance"):
            self.assertEqual(talks._modo({"mode": testo}), "distanza", testo)
        for testo in ("presenza", " In  Presenza ", "PRESENCE", "Local"):
            self.assertEqual(talks._modo({"mode": testo}), "presenza", testo)

    def test_flag_wins_over_generic_fields(self):
        self.assertEqual(talks._modo({"type": "presenza", "flagByDist": True}), "distanza")
        self.assertEqual(talks._modo({"mode": "distanza", "flagByDist": False}), "presenza")

    def test_unrelated_type_does_not_set_mode(self):
        self.assertEqual(talks._modo({"type": "colloquio", "flagByDist": True}), "distanza")
        self.assertEqual(talks._modo({"type": "colloquio"}), "")

    def test_booked_rows_keep_own_mode(self):
        corpo = {"talks": [_prenotato(1, flagByDist=True), _prenotato(2, flagByDist=False),
                           _prenotato(3, flagByDist=None)]}
        voci = talks.prenotati(corpo, SLOT_ID)
        self.assertEqual([v["modalita"] for v in voci], ["distanza", "presenza", ""])

    def test_slot_mode_does_not_change_booked_mode(self):
        slot = {"teachers": [{"teacherId": 11, "teacherName": "Docente A", "flagByDist": True,
                              "frames": []}]}
        voci = talks.prenotati({"talks": [_prenotato(1, flagByDist=False)]}, slot)
        self.assertEqual(voci[0]["modalita"], "presenza")

    def test_available_slot_uses_same_rules(self):
        voce = {"date": "2026-10-22", "type": "presenza", "flagByDist": True}
        self.assertEqual(talks.normalizza(voce)["modalita"], "distanza")


class BookedDetailsTests(unittest.TestCase):
    def test_confirmed_structure_with_many_rows(self):
        corpo = {"talks": [_prenotato(1), _prenotato(2, flagByDist=True), _prenotato(3)]}
        voci = talks.prenotati(corpo, SLOT_ID)
        self.assertEqual(len(voci), 3)
        primo = voci[0]
        self.assertEqual(primo["id"], "101")
        self.assertEqual(primo["data"], (OGGI + timedelta(days=1)).isoformat())
        self.assertEqual((primo["ora_inizio"], primo["ora_fine"]), ("09:00", "09:10"))
        self.assertEqual(primo["aula"], "Aula 4")
        self.assertEqual(primo["modalita"], "presenza")
        self.assertEqual(voci[1]["modalita"], "distanza")
        self.assertEqual(primo["dati"], "")

    def test_date_formats(self):
        casi = {
            "2026-10-22": "2026-10-22", "20261022": "2026-10-22", "2026-10-22T10:30:00": "2026-10-22",
            "22/10/2026": "2026-10-22", "22-10-2026": "2026-10-22",
            "31/02/2026": "", "domani": "", "": "", None: "", 5: "",
        }
        for testo, atteso in casi.items():
            riga = talks.prenotati([_prenotato(talkDate=testo)])[0]
            self.assertEqual(riga["data"], atteso, testo)
            self.assertEqual(riga["stato"], "prenotato")
            self.assertEqual(riga["dati"], "" if atteso else "parziali")

    def test_time_in_date_and_unknown_time(self):
        riga = talks.prenotati([_prenotato(talkDate="2026-10-22T10:30:00", startHour=None)])[0]
        self.assertEqual(riga["ora_inizio"], "10:30")
        riga = talks.prenotati([_prenotato(startHour="mattina", endHour="boh")])[0]
        self.assertEqual((riga["ora_inizio"], riga["ora_fine"]), ("", ""))
        self.assertNotEqual(riga["data"], "")

    def test_malformed_row_does_not_hide_valid_rows(self):
        corpo = {"talks": [_prenotato(1), "testo", None, 7, {"talkDate": "x"}, _prenotato(2)]}
        voci = talks.prenotati(corpo, SLOT_ID)
        self.assertEqual(len(voci), 6)
        self.assertEqual([v["dati"] for v in voci], ["", "parziali", "parziali", "parziali", "parziali", ""])
        ordinate = talks.filtra_ordina(voci, OGGI)
        self.assertEqual(len(ordinate), 6)
        self.assertEqual([v["data"] for v in ordinate][:2], [_voce(1)["data"], _voce(2)["data"]])
        self.assertEqual(talks.conta_prenotati(ordinate), 2)

    def test_subject_by_teacher_id(self):
        voci = talks.prenotati([_prenotato(1), _prenotato(2, teacherId=12), _prenotato(3, teacherId=99),
                                _prenotato(4, teacherId=None)], SLOT_ID)
        # duplicate subjects are joined once, in the order found
        self.assertEqual(voci[0]["materia"], "Materia X, Materia Y, Materia Z")
        self.assertEqual(voci[1]["materia"], "")
        self.assertEqual(voci[2]["materia"], "")
        self.assertEqual(voci[3]["materia"], "")

    def test_subject_join_without_usable_slots(self):
        for slot in (None, [], {"Altro": 1}, "testo"):
            self.assertEqual(talks.prenotati([_prenotato(1)], slot)[0]["materia"], "")

    def test_unisci_joins_subject_from_slots(self):
        slot = {"teachers": [{"teacherId": 11, "subjects": ["Materia X"], "frames": [
            {"date": "2026-10-22", "startTime": "09:00"}]}]}
        voci = talks.unisci(slot, {"talks": [_prenotato(1)]})
        self.assertEqual(voci[-1]["materia"], "Materia X")

    def test_unknown_date_keeps_other_known_fields(self):
        riga = talks.prenotati([_prenotato(talkDate="domani")], SLOT_ID)[0]
        self.assertEqual(riga["data"], "")
        self.assertEqual(riga["docente"], "Docente A")
        self.assertEqual(riga["materia"], "Materia X, Materia Y, Materia Z")
        self.assertEqual((riga["ora_inizio"], riga["ora_fine"]), ("09:00", "09:10"))
        self.assertEqual(riga["dati"], "parziali")
        self.assertEqual(riga["stato"], "prenotato")

    def test_missing_time_or_teacher_is_partial(self):
        for extra in ({"startHour": "mattina"}, {"teacherName": None}):
            riga = talks.prenotati([_prenotato(**extra)], SLOT_ID)[0]
            self.assertEqual(riga["dati"], "parziali")
            self.assertNotEqual(riga["data"], "")

    def test_booked_time_is_not_a_free_slot_time(self):
        slot = {"teachers": [{"teacherId": 11, "subjects": ["Materia X"], "frames": [
            {"date": (OGGI + timedelta(days=1)).isoformat(), "startTime": "15:00"}]}]}
        voci = talks.unisci(slot, {"talks": [_prenotato(1, startHour="09:00", endHour="09:10")]})
        prenotato = [v for v in voci if v["stato"] == "prenotato"][0]
        self.assertEqual((prenotato["ora_inizio"], prenotato["ora_fine"]), ("09:00", "09:10"))

    def test_card_row_layout(self):
        scheda = (_BASE / "www" / "cvv-dashboard-card.js").read_text(encoding="utf-8")
        inizio = scheda.index("_vistaColloqui(ent) {")
        vista = scheda[inizio:scheda.index("_vistaAgenda(ent, soloCompiti", inizio)]
        # same column order as an available row, subject in the main row, no status-only row
        self.assertIn("[c.docente, c.materia]", vista)
        self.assertNotIn("<div class=\"riga-colloquio\">", vista)
        self.assertIn(".riga-colloquio .stato-colloquio { margin-left: auto;", scheda)
        self.assertIn(".colloquio.prenotato .stato-colloquio { color: var(--success-color", scheda)
        self.assertIn("font-weight: 700", scheda[scheda.index(".colloquio.prenotato .stato-colloquio"):][:140])

    def test_range_and_order(self):
        corpo = [_prenotato(28), _prenotato(-1), _prenotato(27), _prenotato(0, startHour="11:00"),
                 _prenotato(0, startHour="08:30"), _prenotato(2)]
        voci = talks.filtra_ordina(talks.prenotati(corpo), OGGI)
        self.assertEqual(
            [(v["data"], v["ora_inizio"]) for v in voci],
            [(_voce(0)["data"], "08:30"), (_voce(0)["data"], "11:00"),
             (_voce(2)["data"], "09:00"), (_voce(27)["data"], "09:00")],
        )
        self.assertEqual(talks.conta_prenotati(voci), 4)

    def test_undated_rows_are_not_counted(self):
        voci = talks.prenotati([_prenotato(1), "x"])
        self.assertEqual(talks.conta_prenotati(talks.filtra_ordina(voci, OGGI)), 1)

    def test_meeting_link_validation(self):
        valido = "https://example.org/meet/abc"
        casi = {
            valido: valido, "http://example.org/m": "http://example.org/m",
            "javascript:alert(1)": "", "ftp://example.org/m": "", "https://": "",
            "example.org/m": "", "https://exa mple.org": "", "": "", None: "", 5: "",
            "https://[bad": "",
        }
        for testo, atteso in casi.items():
            self.assertEqual(talks.link_valido(testo), atteso, testo)
        riga = talks.prenotati([_prenotato(1, live_link=valido)])[0]
        self.assertEqual(riga["link"], valido)
        self.assertTrue(riga["ha_link"])
        for assente in (None, "", "javascript:x"):
            riga = talks.prenotati([_prenotato(1, live_link=assente)])[0]
            self.assertEqual(riga["link"], "")
            self.assertFalse(riga["ha_link"])

    def test_link_lookup_by_id(self):
        voci = talks.prenotati([_prenotato(1, live_link="https://example.org/a"), _prenotato(2)])
        self.assertEqual(talks.link_prenotato(voci, 101), "https://example.org/a")
        self.assertEqual(talks.link_prenotato(voci, "101"), "https://example.org/a")
        self.assertEqual(talks.link_prenotato(voci, 102), "")
        self.assertEqual(talks.link_prenotato(voci, 999), "")
        self.assertEqual(talks.link_prenotato(voci, ""), "")
        self.assertEqual(talks.link_prenotato(None, 101), "")

    def test_messages_are_read_with_the_sender(self):
        voci = talks.prenotati([_prenotato(1, teacherMsg=" Testo A ", myMsg="Testo B")])
        self.assertEqual(voci[0]["messaggi"], [
            {"da": "docente", "testo": "Testo A"}, {"da": "genitore", "testo": "Testo B"},
        ])
        self.assertTrue(voci[0]["ha_messaggi"])
        # the generic field `message` is never read
        riga = talks.prenotati([_prenotato(1, message="Testo C")])[0]
        self.assertEqual(riga["messaggi"], [])
        self.assertFalse(riga["ha_messaggi"])

    def test_missing_or_malformed_messages_are_skipped(self):
        for assente in (None, "", "   ", 5, True, ["x"], {"a": 1}):
            riga = talks.prenotati([_prenotato(1, teacherMsg=assente, myMsg=assente)])[0]
            self.assertEqual(riga["messaggi"], [], repr(assente))
            self.assertFalse(riga["ha_messaggi"])
        self.assertEqual(talks.prenotati([_prenotato(1)])[0]["messaggi"], [])

    def test_message_lookup_by_id_is_exact(self):
        voci = talks.prenotati([_prenotato(1, teacherMsg="Testo A"), _prenotato(2)])
        self.assertEqual(talks.messaggi_prenotato(voci, 101), [{"da": "docente", "testo": "Testo A"}])
        self.assertEqual(talks.messaggi_prenotato(voci, "101"), [{"da": "docente", "testo": "Testo A"}])
        for altro in (102, 999, "", None):
            self.assertEqual(talks.messaggi_prenotato(voci, altro), [])
        self.assertEqual(talks.messaggi_prenotato(None, 101), [])
        # a free slot never has messages
        libero = [{"stato": "disponibile", "id": "101", "messaggi": [{"da": "docente", "testo": "x"}]}]
        self.assertEqual(talks.messaggi_prenotato(libero, 101), [])

    def test_private_fields_never_reach_the_rows(self):
        voci = talks.prenotati([_prenotato(1, **PRIVATI)], SLOT_ID)
        self.assertEqual(set(voci[0]), {
            "id", "docente_id", "data", "ora_inizio", "ora_fine", "docente", "materia",
            "stato", "modalita", "aula", "link", "ha_link", "messaggi", "ha_messaggi", "dati",
        })
        # only the two message fields of a booked talk are read
        self.assertEqual(
            [m["testo"] for m in voci[0]["messaggi"]], ["SEGRETO-8", "SEGRETO-7"]
        )
        self.assertNotIn("SEGRETO-6", repr(voci))
        for n in (1, 2, 3, 4, 5):
            self.assertNotIn(f"SEGRETO-{n}", repr(voci))
        # the free slot rows must not read a message field either
        slot = {"frames": [{"date": "2026-10-22", "startTime": "09:00", **PRIVATI}]}
        self.assertNotIn("SEGRETO", repr(talks.unisci(slot, None)))
        # the log helper shows names and types only
        self.assertNotIn("SEGRETO", talks.descrivi([_prenotato(1, **PRIVATI)]))

    def test_empty_responses(self):
        for vuoto in (None, [], {}, {"talks": []}):
            self.assertEqual(talks.prenotati(vuoto, SLOT_ID), [])

    def test_unknown_top_level_raises(self):
        with self.assertRaises(talks.RispostaNonRiconosciuta):
            talks.prenotati({"altro": [1]})


_BASE = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "cvv_dashboard"


class SourceBoundaryTests(unittest.TestCase):
    """Checks on the source text: HA cannot be imported in these tests."""

    def _funzione(self, nome_file, inizio, fine):
        testo = (_BASE / nome_file).read_text(encoding="utf-8")
        return testo[testo.index(inizio):testo.index(fine, testo.index(inizio))]

    def test_talks_requests_use_only_get(self):
        corpo = self._funzione("api.py", "async def async_fetch_colloqui", "async def leggi_comunicazione")
        self.assertEqual(corpo.count("self._get("), 2)
        for vietato in ("_post", "_put", "_delete", "_patch", "POST", "DELETE"):
            self.assertNotIn(vietato, corpo)

    def test_no_write_command_in_the_card_or_the_websocket(self):
        scheda = (_BASE / "www" / "cvv-dashboard-card.js").read_text(encoding="utf-8")
        vista = scheda[scheda.index("_vistaColloqui(ent)"):scheda.index("_vistaAgenda(")]
        for vietato in ("method:", "fetch(", "prenota", "annulla", "elimina", "invia", "stampa"):
            self.assertNotIn(vietato, vista.lower() if vietato.islower() else vista)
        init = (_BASE / "__init__.py").read_text(encoding="utf-8")
        ws = init[init.index("async def _ws_link_colloquio"):init.index("async def _coordinatore_anno")]
        self.assertIn('vol.Optional("anno")', init)
        self.assertIn('"_anni"', ws)
        self.assertNotIn("_coordinatore_anno(", ws)
        self.assertNotIn("async_refresh", ws)
        self.assertIn("messaggi_prenotato(voci, msg[\"talk_id\"])", ws)
        self.assertNotIn("coordinator.api", ws)
        self.assertNotIn("async_fetch", ws)

    def test_sensor_removes_the_booked_link_from_every_attribute_path(self):
        sensore = (_BASE / "sensor.py").read_text(encoding="utf-8")
        classe = sensore[sensore.index("class TalksSensor"):sensore.index("class AbsencesSensor")]
        # the removal of the booked link does not depend on the `completo` flag
        prima = classe.index('if k not in ("link", "messaggi")')
        self.assertLess(prima, classe.index("if not completo:"))
        self.assertIn("conta_prenotati", classe)

    def test_card_renders_messages_as_text_with_safe_links(self):
        scheda = (_BASE / "www" / "cvv-dashboard-card.js").read_text(encoding="utf-8")
        nodi = scheda[scheda.index("_nodiMessaggio(testo) {"):scheda.index("_caricaLinkAperti(ent) {")]
        self.assertNotIn("innerHTML", nodi)
        self.assertIn("createTextNode", nodi)
        self.assertIn("this._linkRiunione(grezzo)", nodi)
        self.assertIn('a.target = "_blank"', nodi)
        self.assertIn('a.rel = "noopener noreferrer"', nodi)
        self.assertIn("stopPropagation", nodi)
        carica = scheda[scheda.index("_caricaLinkColloquio(box, ent) {"):scheda.index("_vistaColloqui(ent) {")]
        self.assertNotIn("innerHTML", carica)
        self.assertIn("Messaggio del docente:", carica)
        self.assertIn("Messaggio del genitore:", carica)

    def test_logs_never_print_row_values(self):
        for nome in ("api.py", "talks.py", "coordinator.py"):
            testo = (_BASE / nome).read_text(encoding="utf-8")
            for riga in testo.splitlines():
                if "_LOGGER" in riga and ("colloqui" in riga.lower()):
                    for campo in ("live_link", "live_pw", "message", "cellNumber", "emailAddr"):
                        self.assertNotIn(campo, riga)


class RetentionTests(unittest.TestCase):
    def test_coordinator_keeps_last_list_after_a_failure(self):
        testo = (_BASE / "coordinator.py").read_text(encoding="utf-8")
        self.assertIn('data.get("colloqui_stato") not in ("errore", "errore_dati")', testo)
        self.assertIn('data[chiave] = vecchi[chiave]', testo)


if __name__ == "__main__":
    unittest.main()
