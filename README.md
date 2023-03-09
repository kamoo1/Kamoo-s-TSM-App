# TSM Backend
[![Tests and Coverage](https://github.com/kamoo1/TSM-Backend/actions/workflows/python-tests-coverage.yml/badge.svg)](https://github.com/kamoo1/TSM-Backend/actions/workflows/python-tests-coverage.yml)
[![codecov](https://codecov.io/gh/kamoo1/TSM-Backend/branch/main/graph/badge.svg?token=20JNWT1J7X)](https://codecov.io/gh/kamoo1/TSM-Backend)

TSM Backend is a serverless auction data exporter for the Trade Skill Master (TSM) addon in World of Warcraft.

## Work in Progress Notice
Please note that this project is still a work in progress. The realm names in the exported file need to be converted to the correct format before it can be used by TSM. Currently, it contains a concatenated string of all connected realms, which is not supported by TSM. Additionally, more data needs to be gathered to test the accuracy of the exported data.

## Usage
To run the exporter locally, follow these steps:
1. Set the BN_CLIENT_ID and BN_CLIENT_SECRET environment variables.

2. Run the following command:
```bash
python -m ah --db_path ./db --export_path ./export.txt --compress_db {region}
```
Replace {region} with the region you want to export data from.

Alternatively, if you want to run the exporter in Github Actions, follow these steps:
1. Fork this project
2. Adding a new environment named `env_main` with the following secrets:
    - `BN_CLIENT_ID`
    - `BN_CLIENT_SECRET`
3. Modify the parameters in the ./.github/workflows/job.yml file to your liking.

The scheduled workflow utilizes the [GitHub Actions Cache](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) as storage for database files. This means that the workflow will reuse the most recent cache and create a new one with the updated database file after the job is completed. Please note that all caches expire after 7 days, and if the total cache usage for the repository exceeds 10GB, the oldest accessed cache will be removed.
