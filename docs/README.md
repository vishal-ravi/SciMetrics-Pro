# ScienceDirect Journal Scraper

A Python-based tool to extract journal metadata from Elsevier's ScienceDirect platform using the Elsevier Serial Title API combined with web scraping for additional metrics.

## Features

- **API Integration**: Fetches journal data directly from Elsevier's Serial Title API
- **Web Scraping**: Extracts additional metrics not available via API (submission times, acceptance rates, open access statements)
- **Progress Tracking**: Visual progress bar with percentage completion
- **Checkpoint System**: Auto-saves progress every 10 entries
- **Excel Integration**: Saves data to original Excel file as a new sheet
- **Rate Limiting**: Respects API limits with built-in delays

## Extracted Data Fields

| Field | Source | Description |
|-------|--------|-------------|
| `title` | API | Journal title |
| `cite_score` | API | CiteScore metric |
| `cite_score_tracker` | API | CiteScore tracker value |
| `sjr` | API | SCImago Journal Rank |
| `snip` | API | Source Normalized Impact per Paper |
| `publisher` | API | Publisher name |
| `open_access` | API | Open access status (Yes/No) |
| `open_access_type` | API | Type of open access |
| `open_access_statement` | Web | Detailed open access statement |
| `submission_to_first_decision` | Web | Days from submission to first decision |
| `submission_to_decision_after_review` | Web | Days from submission to decision after review |
| `submission_to_acceptance` | Web | Days from submission to acceptance |
| `acceptance_rate` | Web | Journal acceptance rate (%) |
| `subject_areas` | API | Subject categories |
| `coverage_start_year` | API | Coverage start year |
| `coverage_end_year` | API | Coverage end year |

## Prerequisites

- Python 3.8+
- Playwright installed with Chromium browser

## Installation

1. Install required Python packages:
```bash
pip install pandas requests playwright openpyxl
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Configuration

The script uses a hardcoded API key:
```python
API_KEY = '1a1c5dc0003f1f666332f199390ee33b'
```

To use your own API key, replace this value in `journal_scraper_api.py`.

## Input File Format

The script expects an Excel file named `jnlactive.xlsx` with the following columns:
- `Full Title` - Journal title
- `ISSN` - Journal ISSN (required)
- `Shortcut URL` - ScienceDirect journal page URL
- `Product ID` - Product identifier

## Usage

Run the scraper:
```bash
python journal_scraper_api.py
```

## Output Files

| File | Description |
|------|-------------|
| `jnlactive.xlsx` | Original file with new sheet "Journal_Data" |
| `journal_checkpoint_*.xlsx` | Checkpoint files every 10 entries |
| `journal_data_final.xlsx` | Final backup of all data |

## Console Output

The script displays:
- Progress bar showing completion percentage
- Summary statistics (successful/failed entries)
- Checkpoint save confirmations

Example:
```
Progress |████████████████████░░░░░░░░░░░░░░░░░░░░| 45.0% (45/100)

======================================================================
COMPLETE!
======================================================================
Total processed: 100
Successful     : 95
Failed/Skipped : 5
Checkpoints    : 10
======================================================================
```

## API Documentation

- [Elsevier Serial Title API](https://dev.elsevier.com/documentation/SerialTitleAPI)

## Notes

- The script includes a 0.3-second delay between requests to respect API rate limits
- Web scraping uses headless Chromium browser
- Checkpoint files are created every 10 entries for data safety
- If the original Excel file is open, data will be saved to `journal_data_api.xlsx` instead

## Troubleshooting

**Issue**: Playwright browser not found  
**Solution**: Run `playwright install chromium`

**Issue**: API returns 404 errors  
**Solution**: Check that ISSN values are valid and properly formatted

**Issue**: Cannot save to original Excel file  
**Solution**: Close the Excel file before running the script

## Files in This Project

| File | Purpose |
|------|---------|
| `journal_scraper_api.py` | Main scraper script (API + Web scraping) |
| `journal_scraper_manual.py` | Manual scraping script with Playwright |
| `journal_scraper_colors.py` | Color-enhanced console output version |
| `jnlactive.xlsx` | Input Excel file with journal list |
| `screenshots/` | Directory for journal page screenshots |
