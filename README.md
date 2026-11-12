# Guides

[![Test and release](https://github.com/hubra-app/hubra-plugin-guides/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/hubra-app/hubra-plugin-guides/actions/workflows/release.yml?query=branch%3Amain) [![License: all rights reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](LICENSE) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-bitsandbricks-ffdd00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/bitsandbricks)

A plugin for [Hubra](https://hubra.club). How-tos for machines, tools and
everything else the club does ("Lock up the clubhouse", "Set up the bar"),
in Markdown or as a link to a manual or video.

**Version** 2.0.0 · **Works with** Hubra >=0.2.5,<1 · **Plugin id** `guides` · **Module** `guides`

## What it does

- *Guides* (`/app/guides`, right **Read guides**, `guides.guides.read`) lists
  every guide with a search. Each guide has its own page with a table of
  contents built from its `##` headings, and a link to every section.
- Writing (**Write guides**, `guides.guides.write`): a title, the text with a
  preview, a link to a manual or video.
- A guide can belong to an inventory item. The item then lists its guides,
  and `/app/inventory/<id>/guide` opens the item's guide.
- A guide can name the qualification it takes; the page then shows it and
  whether the reader holds it. It is shown, not enforced.

Guides is an add-on of Inventory (`depends: inventory >=2.0,<3`), since its
guides show on the item page; a guide doesn't need an item, though. Items come from the Inventory plugin's queries
(`inventory.items.get`, `inventory.items.list`) and qualifications from the
[Qualifications](https://github.com/hubra-app/hubra-plugin-qualifications)
plugin's (`qualifications.kinds.list`, `qualifications.member.holds`); without
them a guide has neither. When an item is deleted, its guides stay and no
longer belong to an item.

## Qualifications moved out

Up to 1.x Guides also kept qualifications and *Wer kann was*. Those are the
Qualifications plugin now, which takes over their tables and rows. Install
it alongside Guides 2.0 to keep them. See `CHANGELOG.md`.

## Install

Platform admins install it from the Plugin catalogue in manage
(official Marketplace, <https://plugins.hubra.club/index.json>, signed with
the Hubra project key). Clubs then switch it on under Einstellungen → Module.

## Develop

Clone this repository into `plugins/guides` of a Hubra checkout. Its tests
then run with Hubra's (`cd app/backend && pytest ../../plugins/guides`), and
`npm run build:plugin` in `app/frontend` builds its frontend. The workflow
does the same against Hubra's `main` on every push and pull request.

## Releasing

Bump `version` in `plugin.yaml`, add a `## <version>` section to
`CHANGELOG.md` and merge. Then tag the merged commit on main and push the tag:

```sh
git switch main && git pull
git tag v<version> && git push origin v<version>
```

The workflow tests the plugin and builds its frontend, the `plugin-signing`
job signs it after your approval, and only then is the GitHub release
`v<version>` published, with `guides-<version>.zip` and its `.sha256` attached. Files
listed in `.releaseignore` stay out of the zip. Releases are immutable, so a
published version never changes: fix a bad one with a new version.

Source: <https://github.com/hubra-app/hubra-plugin-guides>
