# TSM Backend
[![Tests and Coverage](https://github.com/kamoo1/TSM-Backend/actions/workflows/python-tests-coverage.yml/badge.svg)](https://github.com/kamoo1/TSM-Backend/actions/workflows/python-tests-coverage.yml)
[![codecov](https://codecov.io/gh/kamoo1/TSM-Backend/branch/main/graph/badge.svg?token=20JNWT1J7X)](https://codecov.io/gh/kamoo1/TSM-Backend)[![AH Update](https://github.com/kamoo1/TSM-Backend/actions/workflows/job.yml/badge.svg)](https://github.com/kamoo1/TSM-Backend/actions/workflows/job.yml)

TSM Backend is a serverless auction data updater and exporter for the Trade Skill Master (TSM) addon in World of Warcraft.

## Features
- Updates auction data and stores it in a database.
- Exports auction data to TSM's `AppData.lua` file.
- Supports Retail as well as Classic and Classic WLK
- Updates can be run on Github Actions, database files are shared via Github Releases. You can skip the update step and directly export the data from an existing repository.

## Usage
### Running the Update Locally
To run update locally, follow these steps:
1. Set the `BN_CLIENT_ID` and `BN_CLIENT_SECRET` environment variables.

2. Run the following command:
```bash
python -m ah.updater {region}
```
Replace `{region}` with the region you want to export data from.

### Running the Update in Github Actions
Alternatively, if you want to run the update in Github Actions, follow these steps:
1. Fork this project
2. Adding a new environment named `env_main` with the following secrets:
    - `BN_CLIENT_ID`
    - `BN_CLIENT_SECRET`
3. Modify the parameters in the ./.github/workflows/job.yml file to your liking.

The scheduled workflow utilizes the [GitHub Actions Cache](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) as storage for database files. This means that the workflow will reuse the most recent cache and create a new one with the updated database file after the job is completed. Please note that all caches expire after 7 days if not accessed, and if the total cache usage for the repository exceeds 10GB, the oldest accessed cache will be removed.

### Exporting Auction Data to TSM
To export the auction data to TSM, run the following command:
```bash
python -m ah.tsm_exporter {region} {realm1} {realm2} ...
```
Replace `{region}` with the region you want to export data from and `{realm1}`, `{realm2}`, etc. with the realms you want to export data for.

The exporter will automatically locate TSM's `AuctionDB.lua` file and update it with the latest auction data.

### Exporting with Data from a Custom Repository
Auction data from Github Actions is shared via Github Releases, which means you can
skip the update step and directly export the data from an existing repository.
To do this, run the following command:
```bash
python -m ah.tsm_exporter --repo https://github.com/kamoo1/TSM-Backend tw {realm1} {realm2} ...
```

## Future Plans
- [x] Average historical records by day to reduce database size.
- [x] Add Classic and Classic WLK support.