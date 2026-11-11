"""Guides: how-tos, for an item or on their own.

Items and qualifications belong to other plugins; these tests stand in for
their queries by replacing ``routes._ask``.
"""

from __future__ import annotations

import pytest

from hubra_guides import hooks, routes
from hubra_guides.models import Guide
from tests.helpers import set_modules

G = "/api/v1/guides"


@pytest.fixture(autouse=True)
def on(db, seeded_db):
    set_modules(True, "guides")


@pytest.fixture
def others(monkeypatch):
    """Inventory with the item "Laser cutter" (5) and Qualifications with the
    kind "Laser induction" (7), which the reader holds until soon."""

    def ask(name, actor=None, **data):
        if name == routes.ITEMS_GET:
            return [
                {"id": 5, "name": "Laser cutter", "instruction_required": True}
                for i in data["ids"]
                if i == 5
            ]
        if name == routes.ITEMS_LIST:
            return [{"id": 5, "name": "Laser cutter"}]
        if name == routes.KINDS:
            ids = data.get("ids")
            return [
                {"id": 7, "name": "Laser induction", "valid_months": 24}
                for _ in [0]
                if ids is None or 7 in ids
            ]
        if name == routes.HOLDS:
            return [{"kind_id": 7, "state": "soon"} for k in data["kind_ids"] if k == 7]
        raise AssertionError(name)

    monkeypatch.setattr(routes, "_ask", ask)


def test_a_guide_on_its_own(client, auth_headers, db, seeded_db):
    resp = client.post(
        f"{G}/",
        json={"title": "Lock up the clubhouse", "guide": "# Steps\nLights off."},
    )
    assert resp.status_code == 201, resp.get_json()
    gid = resp.get_json()["id"]
    got = client.get(f"{G}/{gid}").get_json()
    assert got["title"] == "Lock up the clubhouse"
    assert got["itemId"] is None and got["qualification"] is None
    listed = client.get(f"{G}/?q=lights").get_json()["data"]
    assert [g["id"] for g in listed] == [gid]
    assert listed[0]["preview"] == "Lights off."
    assert client.patch(f"{G}/{gid}", json={"title": "Close up"}).status_code == 200
    assert client.get(f"{G}/{gid}").get_json()["title"] == "Close up"
    assert client.delete(f"{G}/{gid}").status_code == 204
    assert client.get(f"{G}/{gid}").status_code == 404


def test_validation(client, auth_headers, db, seeded_db):
    assert client.post(f"{G}/", json={"guide": "no title"}).status_code == 400
    bad_url = {"title": "x", "guideUrl": "http://x"}
    assert client.post(f"{G}/", json=bad_url).status_code == 400
    long_url = {"title": "x", "guideUrl": "https://e.org/" + "a" * 500}
    assert client.post(f"{G}/", json=long_url).status_code == 400
    # Without Inventory and Qualifications, neither can be named.
    assert client.post(f"{G}/", json={"title": "x", "itemId": 5}).status_code == 400
    q = {"title": "x", "qualificationId": 7}
    assert client.post(f"{G}/", json=q).status_code == 400
    assert client.get(f"{G}/items").get_json() == []
    assert client.get(f"{G}/qualification-kinds").get_json() == []


def test_a_guide_for_an_item_names_its_qualification(
    client, auth_headers, db, seeded_db, others
):
    assert client.get(f"{G}/items").get_json() == [{"id": 5, "name": "Laser cutter"}]
    kinds = client.get(f"{G}/qualification-kinds").get_json()
    assert kinds == [{"id": 7, "name": "Laser induction"}]
    assert client.post(f"{G}/", json={"title": "x", "itemId": 6}).status_code == 400
    resp = client.post(
        f"{G}/",
        json={
            "title": "Laser cutter",
            "guideUrl": "https://example.org/manual.pdf",
            "itemId": 5,
            "qualificationId": 7,
        },
    )
    assert resp.status_code == 201, resp.get_json()
    got = resp.get_json()
    assert got["itemName"] == "Laser cutter" and got["instructionRequired"] is True
    assert got["qualification"] == {"id": 7, "name": "Laser induction", "mine": "soon"}
    assert [g["id"] for g in client.get(f"{G}/?itemId=5").get_json()["data"]] == [
        got["id"]
    ]
    assert client.get(f"{G}/?itemId=6").get_json()["data"] == []


def test_a_deleted_item_leaves_its_guide(client, auth_headers, db, seeded_db, others):
    gid = client.post(f"{G}/", json={"title": "Laser", "itemId": 5}).get_json()["id"]
    hooks.on_item_deleted(None, item_id=5)
    db.session.commit()
    assert db.session.get(Guide, gid).item_id is None


def test_reading_and_writing_take_their_rights(client, app, db, seeded_db):
    from tests.settings.test_settings_kv import _login, _make_role_and_member

    app.test_cli_runner().invoke(args=["sync-permissions"])
    tier = seeded_db["tier"]
    _make_role_and_member(
        db, tier, name="Reader", permission_keys=["guides.guides.read"]
    )
    _login(client, "reader@test.ch")
    assert client.get(f"{G}/").status_code == 200
    assert client.post(f"{G}/", json={"title": "x"}).status_code == 403


def test_picking_an_item_takes_the_writers_inventory_rights(
    client, auth_headers, db, seeded_db, monkeypatch
):
    """Inventory refuses the writer (no right to read items there): the
    picker lists nothing and no item can be linked, but a guide already
    linked keeps showing its item and can still be edited."""
    from hubra.core.contracts import CURRENT

    def ask(name, actor=None, **data):
        if name in (routes.ITEMS_GET, routes.ITEMS_LIST):
            if actor is CURRENT:
                return None  # what _ask gives for ActionForbidden
            return [{"id": 5, "name": "Laser cutter", "instruction_required": True}]
        return None

    monkeypatch.setattr(routes, "_ask", ask)
    assert client.get(f"{G}/items").get_json() == []
    assert client.post(f"{G}/", json={"title": "x", "itemId": 5}).status_code == 400
    g = Guide(title="Laser", item_id=5)
    db.session.add(g)
    db.session.commit()
    got = client.get(f"{G}/{g.id}").get_json()
    assert got["itemName"] == "Laser cutter"
    resp = client.patch(f"{G}/{g.id}", json={"title": "Laser!", "itemId": 5})
    assert resp.status_code == 200, resp.get_json()


def test_ask_refused_is_none(monkeypatch):
    from hubra.core.contracts import ActionForbidden

    def refuse(name, **kw):
        raise ActionForbidden("no")

    monkeypatch.setattr(routes, "query", refuse)
    assert routes._ask(routes.ITEMS_LIST) is None


def test_body_must_be_an_object(client, auth_headers, db, seeded_db):
    assert client.post(f"{G}/", json=["x"]).status_code == 400
    gid = client.post(f"{G}/", json={"title": "x"}).get_json()["id"]
    assert client.patch(f"{G}/{gid}", json="x").status_code == 400


def test_search_takes_wildcards_literally(client, auth_headers, db, seeded_db):
    a = client.post(f"{G}/", json={"title": "Lock up"}).get_json()["id"]
    b = client.post(f"{G}/", json={"title": "100% safe_mode"}).get_json()["id"]
    assert [g["id"] for g in client.get(f"{G}/?q=%25").get_json()["data"]] == [b]
    assert [g["id"] for g in client.get(f"{G}/?q=_").get_json()["data"]] == [b]
    assert {g["id"] for g in client.get(f"{G}/?q=o").get_json()["data"]} == {a, b}


def test_the_list_comes_in_pages_by_title(client, auth_headers, db, seeded_db):
    for title in ["delta", "Alpha", "charlie", "Bravo", "echo"]:
        assert client.post(f"{G}/", json={"title": title}).status_code == 201
    first = client.get(f"{G}/?pageSize=2").get_json()
    assert [g["title"] for g in first["data"]] == ["Alpha", "Bravo"]
    assert (first["total"], first["page"], first["totalPages"]) == (5, 1, 3)
    last = client.get(f"{G}/?pageSize=2&page=3").get_json()
    assert [g["title"] for g in last["data"]] == ["echo"]
    # pageSize is kept between 1 and 100, page at 1 or more.
    assert client.get(f"{G}/?pageSize=1000").get_json()["pageSize"] == 100
    assert client.get(f"{G}/?pageSize=0&page=-3").get_json()["page"] == 1
