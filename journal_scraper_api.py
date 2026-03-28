"""
ScienceDirect Journal Scraper - Using Elsevier Serial Title API + Web Scraping
This uses your API key to fetch journal data directly, plus web scraping for
additional metrics like submission times and acceptance rate.

API Documentation: https://dev.elsevier.com/documentation/SerialTitleAPI
"""

import pandas as pd
import requests
import time
import json
import asyncio
import re
import sys
from urllib.parse import quote
from playwright.async_api import async_playwright


def print_progress_bar(current, total, prefix='', length=50):
    """Print a progress bar to console"""
    filled = int(length * current // total)
    bar = '█' * filled + '░' * (length - filled)
    percent = (current / total) * 100
    sys.stdout.write(f'\r{prefix} |{bar}| {percent:.1f}% ({current}/{total})')
    sys.stdout.flush()
    if current == total:
        print()  # New line when complete


def save_checkpoint(results, checkpoint_num):
    """Save checkpoint data to Excel"""
    try:
        temp_df = pd.DataFrame(results)
        temp_df.to_excel(f'journal_checkpoint_{checkpoint_num}.xlsx', index=False)
        return True
    except Exception as e:
        print(f"\n  ⚠ Checkpoint save failed: {e}")
        return False

API_KEY = '1a1c5dc0003f1f666332f199390ee33b'
BASE_URL = 'https://api.elsevier.com/content/serial/title'


def safe_get(data, *keys, default=None):
    """Safely navigate nested dictionaries"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data


async def scrape_journal_page(url):
    """
    Scrape additional journal metrics from the ScienceDirect journal page
    including submission times, acceptance rate, and open access statement.
    
    Args:
        url: Journal page URL
        
    Returns:
        dict: Scraped metrics
    """
    data = {
        'submission_to_first_decision': None,
        'submission_to_decision_after_review': None,
        'submission_to_acceptance': None,
        'acceptance_rate': None,
        'open_access_statement': None,
    }
    
    if not url or pd.isna(url):
        return data
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Navigate to journal page
            await page.goto(str(url), wait_until='networkidle', timeout=60000)
            
            # Wait for content to load
            await page.wait_for_timeout(3000)
            
            # Extract submission times and acceptance rate
            metrics_data = await page.evaluate("""
                () => {
                    const result = {
                        submission_to_first_decision: null,
                        submission_to_decision_after_review: null,
                        submission_to_acceptance: null,
                        acceptance_rate: null,
                        open_access_statement: null
                    };
                    
                    // Look for metrics in various formats
                    const metricSelectors = [
                        '[data-testid="journal-metrics"]',
                        '.journal-metrics',
                        '[class*="metrics"]',
                        '[class*="publication-time"]',
                        '.journal-info'
                    ];
                    
                    // Search for submission times in text
                    document.querySelectorAll('div, span, p, li').forEach(el => {
                        const text = el.textContent.trim();
                        
                        // Submission to first decision
                        if (/submission to first decision/i.test(text)) {
                            const match = text.match(/(\d+)\s*days/i) || 
                                         el.nextElementSibling?.textContent.match(/(\d+)\s*days/i);
                            if (match && !result.submission_to_first_decision) {
                                result.submission_to_first_decision = match[1] + ' days';
                            }
                        }
                        
                        // Submission to decision after review
                        if (/submission to decision after review/i.test(text)) {
                            const match = text.match(/(\d+)\s*days/i) || 
                                         el.nextElementSibling?.textContent.match(/(\d+)\s*days/i);
                            if (match && !result.submission_to_decision_after_review) {
                                result.submission_to_decision_after_review = match[1] + ' days';
                            }
                        }
                        
                        // Submission to acceptance
                        if (/submission to acceptance/i.test(text)) {
                            const match = text.match(/(\d+)\s*days/i) || 
                                         el.nextElementSibling?.textContent.match(/(\d+)\s*days/i);
                            if (match && !result.submission_to_acceptance) {
                                result.submission_to_acceptance = match[1] + ' days';
                            }
                        }
                        
                        // Acceptance rate
                        if (/acceptance rate/i.test(text)) {
                            const match = text.match(/(\d+)%/) || 
                                         text.match/(\d+\s*percent)/i ||
                                         el.nextElementSibling?.textContent.match(/(\d+)%/);
                            if (match && !result.acceptance_rate) {
                                result.acceptance_rate = match[1] + '%';
                            }
                        }
                    });
                    
                    // Open access statement - look for the specific class
                    const oaElements = document.querySelectorAll('.open-statement, .js-open-statement, [class*="open-statement"]');
                    oaElements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text && text.length > 5) {
                            result.open_access_statement = text;
                        }
                    });
                    
                    // Also check for open access in links and badges
                    document.querySelectorAll('a, span, div').forEach(el => {
                        const text = el.textContent.trim();
                        if (/^open access$/i.test(text) || /^hybrid$/i.test(text) || /^gold open access$/i.test(text)) {
                            if (!result.open_access_statement || result.open_access_statement.length < text.length) {
                                result.open_access_statement = text;
                            }
                        }
                    });
                    
                    return result;
                }
            """)
            
            data.update(metrics_data)
            
            await browser.close()
            
    except Exception as e:
        data['scrape_error'] = str(e)
    
    return data


def fetch_journal_data(issn, title=None):
    """
    Fetch journal data from Elsevier Serial Title API using ISSN
    
    Args:
        issn: Journal ISSN (e.g., '1877-0657' or '18770657')
        title: Journal title (for display purposes)
    
    Returns:
        dict: Journal metadata including CiteScore, Impact Factor, etc.
    """
    data = {
        'issn': issn,
        'title': None,
        'cite_score': None,
        'cite_score_tracker': None,
        'sjr': None,
        'snip': None,
        'publisher': None,
        'subject_areas': [],
        'open_access': None,
        'open_access_type': None,
        'coverage_start_year': None,
        'coverage_end_year': None,
        'source_id': None,
        'submission_to_first_decision': None,
        'submission_to_decision_after_review': None,
        'submission_to_acceptance': None,
        'acceptance_rate': None,
        'open_access_statement': None,
        'error': None
    }

    try:
        # Clean ISSN (remove hyphens, spaces)
        clean_issn = str(issn).replace('-', '').replace(' ', '').strip() if issn else None

        if not clean_issn or len(clean_issn) < 8:
            data['error'] = 'Invalid or missing ISSN'
            return data

        # Build API URL
        url = f"{BASE_URL}?issn={clean_issn}&apiKey={API_KEY}"

        # Make request
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 404:
            data['error'] = 'Journal not found in API'
            return data
        elif response.status_code != 200:
            data['error'] = f'API Error {response.status_code}: {response.text[:200]}'
            return data

        # Parse JSON response
        result = response.json()

        # Navigate to entry
        entries = safe_get(result, 'serial-metadata-response', 'entry', default=[])
        if not entries:
            data['error'] = 'No journal data found in API response'
            return data

        entry = entries[0]  # Take first entry

        # ── Extract Basic Info ─────────────────────────────────────────────
        data['title'] = safe_get(entry, 'dc:title')
        data['publisher'] = safe_get(entry, 'dc:publisher')
        data['source_id'] = safe_get(entry, 'source-id')
        data['coverage_start_year'] = safe_get(entry, 'coverageStartYear')
        data['coverage_end_year'] = safe_get(entry, 'coverageEndYear')

        # ── Extract ISSN variants ──────────────────────────────────────────
        data['issn_print'] = safe_get(entry, 'prism:issn')
        data['issn_electronic'] = safe_get(entry, 'prism:eIssn')

        # ── Extract Open Access Info ───────────────────────────────────────
        oa_status = safe_get(entry, 'openaccess')
        if oa_status == '1':
            data['open_access'] = 'Yes'
        elif oa_status == '0':
            data['open_access'] = 'No'
        else:
            data['open_access'] = oa_status

        data['open_access_type'] = safe_get(entry, 'openaccessType')

        # ── Extract Subject Areas ──────────────────────────────────────────
        subject_areas = safe_get(entry, 'subject-area', default=[])
        if isinstance(subject_areas, dict):
            subject_areas = [subject_areas]
        for area in subject_areas:
            if isinstance(area, dict) and '$' in area:
                data['subject_areas'].append(area['$'])

        # ── Extract SNIP (Source Normalized Impact per Paper) ──────────────
        snip_list = safe_get(entry, 'SNIPList', 'SNIP', default=[])
        if isinstance(snip_list, dict):
            snip_list = [snip_list]
        if snip_list:
            latest_snip = snip_list[0]
            if isinstance(latest_snip, dict):
                data['snip'] = safe_get(latest_snip, '$')

        # ── Extract SJR (SCImago Journal Rank) ─────────────────────────────
        sjr_list = safe_get(entry, 'SJRList', 'SJR', default=[])
        if isinstance(sjr_list, dict):
            sjr_list = [sjr_list]
        if sjr_list:
            latest_sjr = sjr_list[0]
            if isinstance(latest_sjr, dict):
                data['sjr'] = safe_get(latest_sjr, '$')

        # ── Extract CiteScore ──────────────────────────────────────────────
        cite_info = safe_get(entry, 'citeScoreYearInfoList', default={})
        data['cite_score'] = safe_get(cite_info, 'citeScoreCurrentMetric')
        data['cite_score_year'] = safe_get(cite_info, 'citeScoreCurrentMetricYear')
        data['cite_score_tracker'] = safe_get(cite_info, 'citeScoreTracker')
        data['cite_score_tracker_year'] = safe_get(cite_info, 'citeScoreTrackerYear')

        # ── Cover Image URL ────────────────────────────────────────────────
        links = safe_get(entry, 'link', default=[])
        if isinstance(links, dict):
            links = [links]
        for link in links:
            if isinstance(link, dict) and link.get('@ref') == 'coverimage':
                data['cover_image_url'] = link.get('@href')
                break

    except requests.exceptions.RequestException as e:
        data['error'] = f'Request Error: {str(e)}'
    except json.JSONDecodeError as e:
        data['error'] = f'JSON Parse Error: {str(e)}'
    except Exception as e:
        data['error'] = f'Error: {str(e)}'

    return data


async def main_async():
    """Main async function to process all journals"""

    # Read Excel file
    excel_path = 'jnlactive.xlsx'
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)

    print(f"Total journals to process: {len(df)}")
    print(f"Columns: {df.columns.tolist()}\n")

    # Check required columns
    if 'Shortcut URL' not in df.columns:
        print("ERROR: 'Shortcut URL' column not found!")
        return

    results = []
    total = len(df)
    checkpoint_count = 0

    print("=" * 70)
    print("FETCHING JOURNAL DATA VIA ELSEVIER SERIAL TITLE API + WEB SCRAPING")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        for idx, row in df.iterrows():
            current_num = idx + 1
            url = row.get('Shortcut URL')
            issn = row.get('ISSN')
            title = row.get('Full Title')

            # Show progress bar
            print_progress_bar(current_num - 1, total, prefix='Progress')

            # Skip if no ISSN
            if pd.isna(issn) or not str(issn).strip():
                # Create empty record for skipped entry
                journal_data = {
                    'issn': issn,
                    'title': title,
                    'cite_score': None,
                    'cite_score_tracker': None,
                    'sjr': None,
                    'snip': None,
                    'publisher': None,
                    'subject_areas': [],
                    'open_access': None,
                    'open_access_type': None,
                    'coverage_start_year': None,
                    'coverage_end_year': None,
                    'source_id': None,
                    'submission_to_first_decision': None,
                    'submission_to_decision_after_review': None,
                    'submission_to_acceptance': None,
                    'acceptance_rate': None,
                    'open_access_statement': None,
                    'error': 'No ISSN provided',
                    'original_title': title,
                    'original_issn': issn,
                    'product_id': row.get('Product ID', ''),
                    'shortcut_url': url
                }
                results.append(journal_data)
                continue

            # Fetch data from API
            journal_data = fetch_journal_data(str(issn).strip(), str(title) if pd.notna(title) else None)

            # Scrape additional data from web page
            if url and not pd.isna(url):
                page = await context.new_page()
                try:
                    await page.goto(str(url), wait_until='networkidle', timeout=60000)
                    await page.wait_for_timeout(3000)

                    # Extract submission times and acceptance rate
                    metrics_data = await page.evaluate("""
                        () => {
                            const result = {
                                submission_to_first_decision: null,
                                submission_to_decision_after_review: null,
                                submission_to_acceptance: null,
                                acceptance_rate: null,
                                open_access_statement: null
                            };

                            // Search for submission times in text
                            document.querySelectorAll('div, span, p, li, td, dd').forEach(el => {
                                const text = el.textContent.trim();

                                // Submission to first decision
                                if (/submission to first decision/i.test(text)) {
                                    const match = text.match(/(\\d+)\\s*days/i) ||
                                                 el.nextElementSibling?.textContent.match(/(\\d+)\\s*days/i) ||
                                                 el.parentElement?.textContent.match(/(\\d+)\\s*days/i);
                                    if (match && !result.submission_to_first_decision) {
                                        result.submission_to_first_decision = match[1] + ' days';
                                    }
                                }

                                // Submission to decision after review
                                if (/submission to decision after review/i.test(text)) {
                                    const match = text.match(/(\\d+)\\s*days/i) ||
                                                 el.nextElementSibling?.textContent.match(/(\\d+)\\s*days/i) ||
                                                 el.parentElement?.textContent.match(/(\\d+)\\s*days/i);
                                    if (match && !result.submission_to_decision_after_review) {
                                        result.submission_to_decision_after_review = match[1] + ' days';
                                    }
                                }

                                // Submission to acceptance
                                if (/submission to acceptance/i.test(text)) {
                                    const match = text.match(/(\\d+)\\s*days/i) ||
                                                 el.nextElementSibling?.textContent.match(/(\\d+)\\s*days/i) ||
                                                 el.parentElement?.textContent.match(/(\\d+)\\s*days/i);
                                    if (match && !result.submission_to_acceptance) {
                                        result.submission_to_acceptance = match[1] + ' days';
                                    }
                                }

                                // Acceptance rate
                                if (/acceptance rate/i.test(text)) {
                                    const match = text.match(/(\\d+)%/) ||
                                                 text.match(/(\\d+)\\s*percent/i) ||
                                                 el.nextElementSibling?.textContent.match(/(\\d+)%/);
                                    if (match && !result.acceptance_rate) {
                                        result.acceptance_rate = match[1] + '%';
                                    }
                                }
                            });

                            // Open access statement - look for the specific class
                            const oaSelectors = [
                                '.open-statement',
                                '.js-open-statement',
                                '.sc-jrAGrp',
                                '[class*="open-statement"]',
                                '[class*="js-open-statement"]'
                            ];

                            for (const selector of oaSelectors) {
                                const elements = document.querySelectorAll(selector);
                                for (const el of elements) {
                                    const text = el.textContent.trim();
                                    if (text && text.length > 3) {
                                        result.open_access_statement = text;
                                        break;
                                    }
                                }
                                if (result.open_access_statement) break;
                            }

                            // Also check for open access in links and badges
                            document.querySelectorAll('a, span, div, button').forEach(el => {
                                const text = el.textContent.trim();
                                if (/^open access$/i.test(text) || /^hybrid$/i.test(text) ||
                                    /^gold open access$/i.test(text) || /^subscription$/i.test(text)) {
                                    if (!result.open_access_statement || result.open_access_statement.length < text.length) {
                                        result.open_access_statement = text;
                                    }
                                }
                            });

                            return result;
                        }
                    """)

                    journal_data.update(metrics_data)
                    await page.close()

                except Exception as e:
                    await page.close()

            # Add original data from Excel
            journal_data['original_title'] = title
            journal_data['original_issn'] = issn
            journal_data['product_id'] = row.get('Product ID', '')
            journal_data['shortcut_url'] = url

            results.append(journal_data)

            # Save checkpoint every 10 entries
            if len(results) % 10 == 0:
                checkpoint_count += 1
                save_checkpoint(results, checkpoint_count)

            # Rate limiting - be nice to the API (0.3 sec delay)
            time.sleep(0.3)

        await browser.close()

    # Print final progress bar
    print_progress_bar(total, total, prefix='Progress')
    print()

    # Save final results to the original Excel file as a new sheet
    result_df = pd.DataFrame(results)

    # Save to original file with new sheet
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            result_df.to_excel(writer, sheet_name='Journal_Data', index=False)
        print(f"✓ Data saved to '{excel_path}' in sheet 'Journal_Data'")
    except Exception as e:
        # If append fails (file might be open or other issue), save as separate file
        output_path = 'journal_data_api.xlsx'
        result_df.to_excel(output_path, index=False)
        print(f"✓ Data saved to '{output_path}' (could not append to original: {e})")

    # Also save checkpoints for safety
    result_df.to_excel('journal_data_final.xlsx', index=False)

    # Summary
    ok = result_df['error'].isna().sum() if 'error' in result_df.columns else len(result_df)
    bad = result_df['error'].notna().sum() if 'error' in result_df.columns else 0

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"Total processed: {len(results)}")
    print(f"Successful     : {ok}")
    print(f"Failed/Skipped : {bad}")
    print(f"Checkpoints    : {checkpoint_count}")
    print("=" * 70)


def main():
    """Entry point - runs async main"""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
