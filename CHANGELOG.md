# Changelog


## Unreleased

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
