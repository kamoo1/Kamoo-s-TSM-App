# Kamoo's TSM App
[![CI](https://github.com/kamoo1/Kamoo-s-TSM-App/actions/workflows/ci.yml/badge.svg)](https://github.com/kamoo1/Kamoo-s-TSM-App/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kamoo1/Kamoo-s-TSM-App/branch/main/graph/badge.svg?token=20JNWT1J7X)](https://codecov.io/gh/kamoo1/Kamoo-s-TSM-App)
[![AH Update](https://github.com/kamoo1/Kamoo-s-TSM-App/actions/workflows/cron.yml/badge.svg)](https://github.com/kamoo1/Kamoo-s-TSM-App/actions/workflows/cron.yml)

Auction data updater and exporter for the Trade Skill Master (TSM) addon in World of Warcraft.

## Features
- Update auction data from BattleNet API.
- Export to TSM's `AppData.lua` file.
- Supports all World of Warcraft versions.
- Scheduled updates via GitHub Actions, shares auction data on GitHub Releases.

## Usage
### Update
Steps:
1. Set the `BN_CLIENT_ID` and `BN_CLIENT_SECRET` environment variables.

2. Run the following command:
```bash
python -m ah.updater {region}
```
Replace `{region}` with the region you want to export data from.

### Update in GitHub Actions
Alternatively, to set up scheduled updates in GitHub Actions, follow these steps:
1. Fork this project.
2. Add a new environment named `env_main` with the following secrets:
    - `BN_CLIENT_ID`
    - `BN_CLIENT_SECRET`
3. Specify the frequency, regions, and game versions to update in `./.github/workflows/job.yml`.

> The scheduled workflow utilizes the [GitHub Actions Cache](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) as storage for database files. This means that the workflow will reuse the most recent cache and create a new one with the updated database file after the job is completed. Please note that all caches expire after 7 days if not accessed, and if the total cache usage for the repository exceeds 10GB, the least recently used cache will be removed.

### Export to TSM
To export the auction data to the `AuctionDB.lua` file used by TSM, run the following command:
```bash
python -m ah.tsm_exporter {region} {realm1} {realm2} ...
```
Replace `{region}` with the region you want to export, and `{realm}` with the realms you want to include.

### Export from a GitHub Repository
You can export directly from a repo with a scheduled update set up.
```bash
python -m ah.tsm_exporter --repo https://github.com/kamoo1/Kamoo-s-TSM-App {region} {realm1} {realm2} ...
```

### UI
A handy UI can be found here:
```bash
python -m ah.ui
```
## FAQ
### Update schedule?
Updates are scheduled to run every 3 hours in this repository.

### What is the *LibRealmInfo* patch?
It addresses unlisted realms in TSM's source files - mostly newer realms in the KR and TW regions, where prices won't load correctly unless patched. You may want to re-apply this patch every time TSM is updated.

### Region sales data?
Region sales data is not available through the Blizzard API; instead, it's collected automatically from users by the official TSM App. However, this feature is not planned for this project for now.

### Retail and Wrath data not scheduled on this repo?
This project aims to cover missing data from the official App. Retail and Wrath data for the US and EU are already provided by the official App.

## Releases
Releases are available on [Releases](https://github.com/kamoo1/Kamoo-s-TSM-App/releases), currently, only Windows is supported.