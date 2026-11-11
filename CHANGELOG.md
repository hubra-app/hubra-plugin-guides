# Changelog

## 2.0.1

Security fixes from the plugin audit.

- The item picker and linking a guide to an item ask Inventory as the
  writer, so they show and accept only items the writer may read in
  Inventory (before, anyone with *Write guides* could list the whole
  inventory). A guide keeps showing the item it is linked to.
- Search takes `%` and `_` literally and at most 200 characters.
- A request body that isn't a JSON object is a 400, not a 500.
- The guide list comes in pages (`page`, `pageSize`, at most 100), sorted
  by title in the database; the answer is `{data, total, page, pageSize,
  totalPages}` instead of a plain list. The Guides page has paging.
- Images in a guide show as links instead of loading from the other site,
  which would tell that site who reads the guide and when.

## 2.0.0

Guides are how-tos now, for an item or on their own, and qualifications are
their own plugin.

- A guide has a title and stands on its own; it may belong to an inventory
  item. New page *Guides* (`/app/guides`) lists and searches them; each guide
  has its page at `/app/guides/<id>`. The item shows its guides and links to
  write one; `/app/inventory/<id>/guide` still opens the item's guide.
- Every item's guide is copied into the new table `guides`, titled with the
  item's name. `item_guides` stays for now; a later release drops it.
- Qualifications and *Wer kann was* moved to the new plugin
  [Qualifications](https://github.com/hubra-app/hubra-plugin-qualifications)
  1.0.0, which takes over `qualification_kinds` and `member_qualifications`
  with their rows. Install it together with this update. Removing Guides
  never removes those tables.
- Still an add-on of Inventory (for the item page), but it imports nothing
  from it: items and qualifications come from the other plugins' queries;
  a deleted item leaves its guides without an item.
- The module is `guides` now (was `inventory.guides`). Clubs that had Guides
  on keep it on (`renamed_from`); this needs the Hubra release with
  hubra-app/hubra#278. The rights `guides.guides.read`/`write` stay.
- API: `GET/POST /guides/`, `GET/PATCH/DELETE /guides/<id>`,
  `GET /guides/items`, `GET /guides/qualification-kinds`. The 1.x
  `GET/PUT /guides/<item_id>` and `/guides/qualifications/*` are gone.
- Gives the standard roles access when a club first switches it on
  (`role_defaults`): Mitglied Ansehen, Vorstand Bearbeiten. Needs Hubra 0.2.5
  or later.

## 1.6.0

- Gives the standard roles access when a club first switches it on (`role_defaults`, docs/roles.md in hubra-app/hubra): Mitglied Ansehen, Vorstand Bearbeiten. Roles without access don't see it; their own data from it stays on their profile. Needs Hubra 0.2.5 or later.

## 1.5.2

1.5.1 was tagged but couldn't be signed, so it was never released. 1.5.2 is the same plugin, signed. What it brings:

- Who can do what: qualification types can let members add them to
  themselves (`selfService`). Every member sees and searches those under
  *Wer kann was* (`/app/skills`) and adds, changes or removes their own, there
  or on their account page; a new name adds a new self-service type. The
  club's own types stay with the managers. A self-service type cannot be what
  an item takes.
- Another member can confirm ("Bestätigen") someone's self-service entry;
  the card then shows "Bestätigt von …" and the holder gets a notification.
  Changing the note clears it; the confirmer or a manager can take it back.
- New API: `POST/PATCH/DELETE /qualifications/mine`, `GET /qualifications/directory`,
  `POST/DELETE /qualifications/<id>/confirm`.
- Columns `qualification_kinds.self_service`,
  `member_qualifications.confirmed_by`/`confirmed_at`. The migration copies the
  Community plugin's "Kann" entries (`community_skills`, kind `skill`) into
  self-service qualifications, if that table exists.

## 1.5.1

1.5.0 was tagged but couldn't be signed, so it was never released. 1.5.1 is the same plugin, signed. What 1.5.0 brings:

- Who can do what: qualification types can let members add them to
  themselves (`selfService`). Every member sees and searches those under
  *Wer kann was* (`/app/skills`) and adds, changes or removes their own, there
  or on their account page; a new name adds a new self-service type. The
  club's own types stay with the managers. A self-service type cannot be what
  an item takes.
- Another member can confirm ("Bestätigen") someone's self-service entry;
  the card then shows "Bestätigt von …" and the holder gets a notification.
  Changing the note clears it; the confirmer or a manager can take it back.
- New API: `POST/PATCH/DELETE /qualifications/mine`, `GET /qualifications/directory`,
  `POST/DELETE /qualifications/<id>/confirm`.
- Columns `qualification_kinds.self_service`,
  `member_qualifications.confirmed_by`/`confirmed_at`. The migration copies the
  Community plugin's "Kann" entries (`community_skills`, kind `skill`) into
  self-service qualifications, if that table exists.

## 1.5.0

- Who can do what: qualification types can let members add them to
  themselves (`selfService`). Every member sees and searches those under
  *Wer kann was* (`/app/skills`) and adds, changes or removes their own, there
  or on their account page; a new name adds a new self-service type. The
  club's own types stay with the managers. A self-service type cannot be what
  an item takes.
- Another member can confirm ("Bestätigen") someone's self-service entry;
  the card then shows "Bestätigt von …" and the holder gets a notification.
  Changing the note clears it; the confirmer or a manager can take it back.
- New API: `POST/PATCH/DELETE /qualifications/mine`, `GET /qualifications/directory`,
  `POST/DELETE /qualifications/<id>/confirm`.
- Columns `qualification_kinds.self_service`,
  `member_qualifications.confirmed_by`/`confirmed_at`. The migration copies the
  Community plugin's "Kann" entries (`community_skills`, kind `skill`) into
  self-service qualifications, if that table exists.

## 1.4.0

- Qualifications with expiry: types with a validity and reminder days, who
  holds which until when, renewals, a daily reminder to the holder and the
  managers, "My qualifications" on the account page. A guide can name the
  qualification its item takes and shows whether the reader holds it.
  New permission `guides.qualifications.manage`; tables `qualification_kinds`,
  `member_qualifications`; column `item_guides.qualification_id`.
- Guides no longer imports Inventory or reads its tables: items come from
  Inventory's query `inventory.items.get`, and a deleted item's guide is
  removed when Inventory sends `inventory.item.deleted`. Fixes the CI check
  against imports from other plugins. Needs Hubra with contracts
  (hubra-app/hubra#231) and an Inventory that offers them
  (hubra-app/hubra-plugin-inventory#7).
- plugin.yaml lists the areas it uses (`uses:`).

## 1.3.1

- Release on a pushed v* tag (works with immutable releases) (#8)

## 1.3.0

- A guide is now a page of its own, /app/inventory/<id>/guide, instead of
  the foot of the item's side panel: the guide at reading width, a table of
  contents beside it (a folding "Inhalt" list on phones) that follows where
  you are, and a link back to the item.
- Each `##`/`###` heading gets a link of its own (`…/guide#laengsschnitt`).
- The item panel shows a short preview with "Read guide", "Open manual" and
  "Edit"; guides are written on the page, with a preview.
- German texts are standard German like the rest of the app ("Anleitung",
  not "Aaleitig").

## 1.2.0

- Works with the Inventory plugin. Inventory is no longer built into Hubra;
  Guides still needs it and now finds it in either place.

## 1.1.0

Built for Hubra 0.2 (Mantine 9, plugin host API 2). Needs Hubra 0.2 or newer.

## 1.0.1

- A deleted inventory item's guide can no longer be read or saved.
- A guide link over 500 characters is refused with a 400 instead of failing.

## 1.0.0

First release as a plugin. Before, Guides was built into Hubra.
