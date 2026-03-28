"""
ScienceDirect Journal Scraper - Manual Browser Mode
This opens a REAL browser window that YOU control.

HOW TO USE:
1. Run this script: python journal_scraper_manual.py
2. A Chrome browser window will open
3. Browse to the journal URL shown in the terminal
4. Wait for the page to fully load (you should see journal title, CiteScore, Impact Factor)
5. Press ENTER in the terminal to capture the data
6. The script will extract data via JavaScript and save screenshot
7. The browser will navigate to the next URL automatically
8. Repeat until all journals are processed

The script saves progress after each journal so you can stop anytime.
"""

import pandas as pd
import asyncio
import os
from playwright.async_api import async_playwright


# JavaScript to extract data from the loaded page
JS_EXTRACT = """
() => {
    const result = {
        title: null,
        citeScore: null,
        impactFactor: null,
        openAccess: [],
        coverImageUrl: null
    };

    // Try multiple title selectors
    const titleSelectors = [
        '#journal-title',
        'h1.js-title-text a',
        'h1 a.js-title-link',
        'h1 a[usagezone="jrnl_banner"]',
        'h1'
    ];
    for (const sel of titleSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim()) {
            result.title = el.textContent.trim();
            break;
        }
    }

    // CiteScore
    const csEl = document.querySelector('div.js-cite-score span.text-l, [class*="js-cite-score"] span.text-l');
    if (csEl) result.citeScore = csEl.textContent.trim();

    // Impact Factor
    const ifEl = document.querySelector('div.js-impact-factor span.text-l, [class*="js-impact-factor"] span.text-l');
    if (ifEl) result.impactFactor = ifEl.textContent.trim();

    // Open Access
    document.querySelectorAll('span.js-open-statement-text, [class*="open-statement-text"]').forEach(el => {
        const txt = el.textContent.trim();
        if (txt) result.openAccess.push(txt);
    });

    // Cover Image
    const imgEl = document.querySelector('img.cover-image, img.js-cover-image');
    if (imgEl) result.coverImageUrl = imgEl.src;

    return result;
}
"""


async def process_journal(page, url, idx, total, screenshots_dir):
    """Navigate to URL and wait for user to confirm page is loaded, then extract data."""
    record = {
        'url': url,
        'title': None,
        'cite_score': None,
        'impact_factor': None,
        'open_access': None,
        'cover_image_url': None,
        'screenshot': None,
        'error': None
    }

    try:
        print(f"\n{'='*60}")
        print(f"[{idx}/{total}] Navigate to:")
        print(f"  {url}")
        print(f"{'='*60}")

        # Navigate to the URL
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(2000)

        print("\n>>> Browser is loading the page...")
        print(">>> Please wait for the journal page to fully load")
        print(">>> You should see: Journal Title, CiteScore, Impact Factor")
        print(">>> \n>>> Press ENTER when ready to capture data...")

        # Wait for user to press ENTER
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, f"journal_{idx:04d}.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        record['screenshot'] = screenshot_path
        print(f"  Screenshot saved: {screenshot_path}")

        # Extract data via JavaScript
        data = await page.evaluate(JS_EXTRACT)

        record['title'] = data.get('title')
        record['cite_score'] = data.get('citeScore')
        record['impact_factor'] = data.get('impactFactor')
        record['open_access'] = ' | '.join(data.get('openAccess', []))
        record['cover_image_url'] = data.get('coverImageUrl')

        print(f"\n  ✓ Title        : {record['title'] or 'NOT FOUND'}")
        print(f"  ✓ CiteScore    : {record['cite_score'] or 'NOT FOUND'}")
        print(f"  ✓ Impact Factor: {record['impact_factor'] or 'NOT FOUND'}")
        print(f"  ✓ Open Access  : {record['open_access'] or 'NOT FOUND'}")

        # Check if we got blocked
        if not record['title'] or 'problem providing' in (record['title'] or '').lower():
            record['error'] = 'Page blocked or not loaded properly'
            print("\n  ⚠ WARNING: Page appears to be blocked!")

    except Exception as e:
        record['error'] = str(e)
        print(f"  ✗ ERROR: {e}")

    return record


async def main():
    # ── Read Excel ─────────────────────────────────────────────────────────
    excel_path = 'jnlactive.xlsx'
    df = pd.read_excel(excel_path)
    print(f"\nLoaded {len(df)} journals from {excel_path}")

    if 'Shortcut URL' not in df.columns:
        print("ERROR: 'Shortcut URL' column not found!")
        return

    # ── Create output folders ──────────────────────────────────────────────
    screenshots_dir = 'screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)

    results = []
    total = len(df)

    print("\n" + "="*60)
    print("MANUAL BROWSER MODE")
    print("="*60)
    print("A Chrome browser window will open.")
    print("You control the browser - navigate, wait for pages to load.")
    print("Press ENTER in this terminal to capture data from each page.")
    print("="*60 + "\n")

    async with async_playwright() as p:
        # Launch VISIBLE browser (headless=False)
        browser = await p.chromium.launch(
            headless=False,  # <-- This opens a real browser window
            args=['--start-maximized']
        )

        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900}
        )
        page = await context.new_page()

        try:
            for idx, row in df.iterrows():
                url = row.get('Shortcut URL')

                if pd.isna(url) or not str(url).strip():
                    print(f"\n[{idx+1}/{total}] Skipping: empty URL")
                    continue

                record = await process_journal(
                    page, str(url).strip(), idx + 1, total, screenshots_dir
                )

                # Merge with original Excel data
                record['full_title'] = row.get('Full Title', '')
                record['issn'] = row.get('ISSN', '')
                record['product_id'] = row.get('Product ID', '')

                results.append(record)

                # Save progress
                pd.DataFrame(results).to_excel('journal_data_progress.xlsx', index=False)
                print(f"\n  >> Progress saved ({len(results)} of {total} done)")

                # Ask if user wants to continue
                if idx < len(df) - 1:
                    print("\n>>> Press ENTER to continue to next journal...")
                    await asyncio.get_event_loop().run_in_executor(None, input)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
        finally:
            await browser.close()

    # ── Final save ─────────────────────────────────────────────────────────
    result_df = pd.DataFrame(results)
    output_path = 'journal_data_scraped.xlsx'
    result_df.to_excel(output_path, index=False)

    ok = result_df['error'].isna().sum()
    bad = result_df['error'].notna().sum()

    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"Output file  : {output_path}")
    print(f"Screenshots  : {screenshots_dir}/")
    print(f"Successful   : {ok}")
    print(f"Failed       : {bad}")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
