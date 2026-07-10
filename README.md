# Warframe Trade Optimizer

Warframe Trade Optimizer is a small automation project designed to help you monitor Warframe Market prices for Prime Warframes and identify potentially profitable trading opportunities.

The project scrapes market data for one or several Warframes, compares the cost of buying a full Prime set versus buying its individual parts, and can send the best opportunities to Discord through a webhook.

## What the project does

This project is built around a simple data pipeline:

1. A Python extractor scrapes Warframe Market data for a given Warframe.
2. The script gathers the prices of the full Prime set and its main components.
3. It writes the results to a JSON file.
4. A GitHub Actions workflow runs this extraction for many Warframes in parallel.
5. The generated JSON files are collected and processed to produce Discord notifications.

The main goal is to automate the collection of market data and make it easier to compare full-set purchases with buying pieces separately.

## Project structure

- [extract-wfm.py](extract-wfm.py): Python script used by the data extraction pipeline to collect prices for one Warframe and write a JSON result file
- [notify.py](notify.py): Python script that reads the generated JSON files and sends the best trade opportunities to Discord
- [requirements.txt](requirements.txt): Python dependencies needed to run the scripts
- [setup.sh](setup.sh): optional helper script to prepare a local Python environment on Linux/macOS
- [setup.ps1](setup.ps1): optional helper script to prepare a local Python environment on Windows
- [.github/workflows/wf-market.yml](.github/workflows/wf-market.yml): GitHub Actions workflow that runs the extraction pipeline and transfers the JSON data between jobs

## Local development environment

The setup scripts are only there to help you prepare a local Python environment on your machine.
They are not the core of the project.

The real value of the repository is the data workflow:

- the Python code extracts market data,
- the workflow executes that code in CI,
- and the JSON files are passed between steps/jobs as artifacts.

## Requirements

- Python 3.11 or newer
- pip
- Playwright
- Chromium browser for Playwright

## Local setup (optional)

If you want to work on the project locally, you can use one of the setup scripts:

On Linux/macOS:

```bash
bash setup.sh
```

On Windows PowerShell:

```powershell
./setup.ps1
```

These scripts simply create a local Python environment and install the required packages.

## Usage

### 1. Run the extractor for one Warframe

```bash
python extract-wfm.py yareli
```

This generates a JSON file such as:

```text
result_yareli.json
```

### 2. Run the Discord notification step

Set your webhook URL:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

Then run:

```bash
python notify.py
```

This reads the JSON files produced by the extraction step and sends the top trade opportunities to Discord.

## GitHub Actions workflow

The workflow in [.github/workflows/wf-market.yml](.github/workflows/wf-market.yml) is the main automation layer of the project.

It performs the following flow:

1. Starts one job per Warframe in a matrix
2. Runs the Python extractor for that Warframe
3. Saves the resulting JSON file as an artifact
4. Downloads all artifacts in a later job
5. Aggregates the data and sends the notification to Discord

This is the core data pipeline of the repository.

## Notes

- The extractor uses the official Warframe Market API and filters for PC, ingame, sell orders.
- The project is intended for automation, market analysis, and personal trading research.
- You can modify the list of Warframes in the workflow if you want to expand or reduce the scope of the extraction.

## Example

If buying the individual Prime parts is more interesting than buying the full Prime set, the pipeline will surface that opportunity and provide a ready-to-use whisper message.
