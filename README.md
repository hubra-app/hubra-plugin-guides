# Guides

[![Test and release](https://github.com/hubra-app/hubra-plugin-guides/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/hubra-app/hubra-plugin-guides/actions/workflows/release.yml?query=branch%3Amain) [![License: all rights reserved](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)](LICENSE)

A plugin for [Hubra](https://hubra.club). A usage guide per machine or tool, in Markdown or as a link to a manual or video, shown on the inventory item.

**Version** 1.5.0 · **Works with** Hubra >=0.2,<1 · **Plugin id** `guides`

## Qualifications

Trainer licences, first aid, machine inductions: *Qualifications* (permission
**Manage qualifications**, `guides.qualifications.manage`) lists who holds
which and until when, soonest expiry first, with filters for "expires soon"
and "expired".

- A qualification type has a validity in months (empty: it does not expire)
  and how many days before expiry to remind.
- Entering one again for the same member renews it.
- A daily job notifies the holder and everyone who manages qualifications once
  before it expires; a renewal arms the reminder again.
- Members see their own under *My qualifications* on their account page.
- A guide can name the qualification its item takes; the guide then shows it,
  and whether the reader holds it.

## Who can do what

What members can do for the club (electrician, graphic design, first aid
outside the club's own courses) are qualifications too: types switched to
"Members add it themselves". *Wer kann was* (`/app/skills`, every member)
lists who has which, with a search; members add their own there or on their
account page, picking a type or typing a new one, and change or remove only
their own. Managers still see and edit everything under *Qualifications*.
A self-service type can never be what an item takes, since nobody checked it.

This replaces the "Kann" entries of the Community plugin's skills directory:
updating to 1.5.0 copies them here once (when that table exists; Guides does
not need Community).

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
