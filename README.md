# 📚 SciMetrics Pro - ScienceDirect Journal Intelligence Suite

A comprehensive Python-based toolkit for extracting journal metadata from Elsevier's ScienceDirect platform. This project combines API integration with web scraping techniques to collect detailed journal metrics and information.

## 🚀 Overview

This project provides multiple scraping approaches to extract comprehensive journal data including:
- **API Integration**: Direct data fetch from Elsevier's Serial Title API
- **Web Scraping**: Extraction of additional metrics not available via API
- **Manual Browser Control**: Interactive scraping with real browser control
- **Color Analysis**: Extraction of visual styling information from journal pages

## 📁 Project Structure

```
Science_Direct/
├── README.md                    # This file
├── journal_scraper_api.py       # Main API + web scraping script
├── src/                         # Source code directory
│   ├── journal_scraper_api.py   # Main scraper (API + Web)
│   ├── journal_scraper_manual.py # Manual browser control scraper
│   └── journal_scraper_colors.py # Color extraction scraper
├── data/                        # Data directories
│   ├── checkpoints/             # Auto-save checkpoint files
│   ├── input/                   # Input Excel files
│   └── output/                  # Output results
├── docs/                        # Documentation
│   └── README.md               # Original documentation
├── assets/                      # Static assets
└── .qoder/                      # Configuration directory
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Microsoft Excel (for viewing output files)

### Install Dependencies

```bash
# Install required Python packages
pip install pandas requests playwright openpyxl playwright-stealth

# Install Playwright browsers
playwright install chromium
```

## 📊 Available Scrapers

### 1. API + Web Scraper (`journal_scraper_api.py`)

**Primary scraper** that combines Elsevier API data with web scraping for comprehensive metrics.

**Features:**
- Fetches journal metadata via Elsevier Serial Title API
- Scrapes additional metrics from journal web pages
- Progress tracking with visual progress bars
- Automatic checkpoint system (every 10 entries)
- Rate limiting to respect API limits

**Extracted Data:**
- Basic metadata (title, publisher, ISSN)
- Impact metrics (CiteScore, SJR, SNIP)
- Submission timelines (first decision, acceptance)
- Acceptance rates
- Open access information
- Subject areas and coverage years

### 2. Manual Browser Scraper (`src/journal_scraper_manual.py`)

**Interactive scraper** that provides manual control over the browsing process.

**Features:**
- Opens real browser window for user control
- Interactive data capture with ENTER key
- Screenshot capture for each journal
- Progress saving after each entry
- Ideal for handling anti-bot measures

### 3. Color Extraction Scraper (`src/journal_scraper_colors.py`)

**Specialized scraper** focused on extracting visual styling information.

**Features:**
- Extracts color values from journal pages
- Analyzes title and open access statement colors
- Comprehensive metadata extraction
- Stealth mode for anti-bot evasion

## 📋 Input Requirements

All scrapers expect an Excel file named `jnlactive.xlsx` with the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| `Full Title` | No | Journal title (for reference) |
| `ISSN` | Yes | Journal ISSN number (required for API) |
| `Shortcut URL` | Yes | ScienceDirect journal page URL |
| `Product ID` | No | Product identifier |

## 🚀 Usage

### Quick Start

1. **Prepare your input file** (`jnlactive.xlsx`) with the required columns
2. **Choose your scraper** based on your needs:
   ```bash
   # Main API + Web scraper (recommended)
   python journal_scraper_api.py
   
   # Manual browser control
   python src/journal_scraper_manual.py
   
   # Color extraction
   python src/journal_scraper_colors.py
   ```

### API Configuration

The main scraper uses an Elsevier API key. Update it in `journal_scraper_api.py`:

```python
API_KEY = 'your_api_key_here'
```

Get your API key from: [Elsevier Developer Portal](https://dev.elsevier.com/)

## 📤 Output Files

| File | Description |
|------|-------------|
| `jnlactive.xlsx` | Original file with new "Journal_Data" sheet |
| `journal_checkpoint_*.xlsx` | Auto-save checkpoints every 10 entries |
| `journal_data_final.xlsx` | Complete backup of all extracted data |
| `journal_data_api.xlsx` | Fallback output if original file is locked |

## 📊 Extracted Data Fields

### API Data Fields
- `title` - Journal title
- `cite_score` - Current CiteScore metric
- `cite_score_tracker` - CiteScore tracker value
- `sjr` - SCImago Journal Rank
- `snip` - Source Normalized Impact per Paper
- `publisher` - Publisher name
- `subject_areas` - Subject categories
- `coverage_start_year` / `coverage_end_year` - Publication coverage
- `open_access` - Open access status
- `open_access_type` - Type of open access

### Web Scraped Fields
- `submission_to_first_decision` - Days to first decision
- `submission_to_decision_after_review` - Days to decision after review
- `submission_to_acceptance` - Days to acceptance
- `acceptance_rate` - Journal acceptance rate (%)
- `open_access_statement` - Detailed open access description

### Color Extraction Fields
- `titleColor` - RGB color of journal title
- `openAccessColor` - RGB color of open access statement
- `coverImageUrl` - URL to journal cover image

## 🔧 Configuration Options

### Rate Limiting
The main scraper includes built-in rate limiting:
```python
time.sleep(0.3)  # 300ms delay between requests
```

### Checkpoint Frequency
Auto-saves every 10 entries (configurable in code):
```python
if len(results) % 10 == 0:
    save_checkpoint(results, checkpoint_count)
```

### Browser Settings
Playwright uses headless Chromium with custom user agent:
```python
user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
```

## 🛡️ Error Handling

The scrapers include comprehensive error handling:
- **API Errors**: 404, rate limits, network timeouts
- **Scraping Errors**: Page load failures, missing elements
- **File I/O Errors**: Excel file locks, permission issues
- **Browser Errors**: Playwright failures, navigation timeouts

## 📈 Console Output

### Progress Tracking
```
Progress |████████████████████░░░░░░░░░░░░░░░░░░░░| 45.0% (45/100)
```

### Completion Summary
```
======================================================================
COMPLETE!
======================================================================
Total processed: 100
Successful     : 95
Failed/Skipped : 5
Checkpoints    : 10
======================================================================
```

## � Docker Deployment

### Quick Start with Docker

1. **Prepare your input file** (`jnlactive.xlsx`) in the project root
2. **Build and run the main scraper:**
   ```bash
   docker-compose up --build
   ```

### Available Docker Services

#### Main API + Web Scraper
```bash
# Default service
docker-compose up --build

# Or explicitly
docker-compose --profile main up --build
```

#### Manual Browser Scraper
```bash
docker-compose --profile manual up --build
```

#### Color Extraction Scraper
```bash
docker-compose --profile colors up --build
```

### Docker Configuration

#### Environment Variables
```bash
# Set custom API key
API_KEY=your_api_key_here docker-compose up --build

# Or create .env file
echo "API_KEY=your_api_key_here" > .env
```

#### Volume Mounts
The Docker containers automatically mount:
- `./data` → `/app/data` (checkpoints, input, output)
- `./jnlactive.xlsx` → `/app/jnlactive.xlsx` (read-only)
- `./screenshots` → `/app/screenshots` (for manual scraper)

### Docker Commands

#### Build Only
```bash
docker-compose build
```

#### Run in Background
```bash
docker-compose up -d --build
```

#### View Logs
```bash
docker-compose logs -f
```

#### Stop Services
```bash
docker-compose down
```

#### Clean Up
```bash
# Remove containers and networks
docker-compose down

# Remove images too
docker-compose down --rmi all
```

### Production Deployment

#### With Custom Configuration
```bash
# Create production override
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

#### Resource Limits
```yaml
# Add to docker-compose.yml for production
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

## �🔍 Troubleshooting

### Docker Issues

**Issue**: Playwright browsers not found in container  
**Solution**: Rebuild the image (browsers are pre-installed)
```bash
docker-compose build --no-cache
```

**Issue**: Permission errors with output files  
**Solution**: Ensure proper volume permissions
```bash
sudo chown -R 1000:1000 ./data ./screenshots
```

**Issue**: Container exits immediately  
**Solution**: Check logs and ensure input file exists
```bash
docker-compose logs scimetrics-pro
```

**Issue**: API rate limiting in container  
**Solution**: Adjust rate limiting in code or use multiple containers

### Common Issues

**Issue**: Playwright browser not found (local)  
**Solution**: `playwright install chromium`

**Issue**: API returns 404 errors  
**Solution**: Verify ISSN format and API key validity

**Issue**: Cannot save to Excel file  
**Solution**: Close Excel file before running script

**Issue**: Web scraping blocked  
**Solution**: Use manual scraper or increase delays

**Issue**: Missing dependencies  
**Solution**: Ensure all required packages are installed

### Debug Mode
Enable verbose logging by modifying the script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Documentation

- [Elsevier Serial Title API](https://dev.elsevier.com/documentation/SerialTitleAPI)
- [Playwright Documentation](https://playwright.dev/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect Elsevier's terms of service and API usage limits.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the console output for error messages
3. Verify input file format and API configuration
4. Test with a small subset of journals first

---

**Note**: This tool is designed for legitimate research and data collection purposes. Always ensure compliance with the target website's terms of service and applicable data protection regulations.
