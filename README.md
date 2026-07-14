# Reactivation Report

Identify hosted players who have fallen below their normal play patterns. 

## Requirements

You need:

- Windows
- Python 3.11 or newer

## Set up the app

1. Download the latest release.
2. Extract the ZIP to a local folder.
3. Double-click `setup_and_run_gui.bat`.

Setup creates a per-user Python environment and opens the app. For weekly use, double-click `run_gui.bat`.

Run setup again after each update. If setup or launch fails, run `check_env.bat`.

## Create the report

### Step 1: Upload reports

Open the app with `run_gui.bat`. Select this week's Hosted Players CSV and last week's workbook. Click **Find reactivated players**.

### Step 2: Send UIDs to Tableau

Paste the copied UIDs into Tableau, then export the Reactivated Players CSV. If the app finds no missing UIDs, skip the paste and continue with the export.

### Step 3: Add the export

Return to the app. Use the most recent reactivated players CSV or choose another file.

### Step 4: Open the report

The app builds and validates the workbook. Click **Open workbook** when it finishes.

```text
<Market> - Hosted Players Report MM.DD.YY.xlsx
```

## Use the command line

For most tasks, use the GUI. Use the CLI for troubleshooting or repeatable runs.

Run this command from the extracted app folder:

```bat
"%LOCALAPPDATA%\HostedPlayersReport\.venv\Scripts\python.exe" cli.py ^
  --hosted-csv "C:\Path\To\Hosted Players.csv" ^
  --last-week-xlsx "C:\Path\To\Last Week.xlsx" ^
  --reactivated-csv "C:\Path\To\Re-Engagement.csv"
```

See all options:

```bat
"%LOCALAPPDATA%\HostedPlayersReport\.venv\Scripts\python.exe" cli.py --help
```

## Troubleshoot

- **Missing Python:** Run `check_env.bat`. Install Python 3.11 or newer, or set `HOSTED_PLAYERS_PYTHON` to the full path of `python.exe`.
- **Locked workbook:** Close it in Excel, wait for OneDrive to finish syncing, then retry.
- **CSV file not accepted:** Export the file from Tableau as UTF-16 tab-delimited text.
- **Native PivotTables fail:** Install desktop Excel and rerun setup. The app can still create static summary sheets.
- **Support:** Send `%APPDATA%\HostedPlayersReport\app.log` and the diagnostic ID shown by the app.
