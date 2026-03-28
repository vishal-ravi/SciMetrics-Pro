"""
ScienceDirect Journal Scraper - Extracts Colors from Website
Uses Playwright to navigate to each journal URL and extract color values via JavaScript

Extracts:
- Title color (from h1.js-title-text style)
- Open access text color (from span.js-open-statement-text)
- All other journal metadata
"""

import pandas as pd
import asyncio
import os
import re
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth


# JavaScript to extract colors and all data from the page
JS_EXTRACT_COLORS = """
() => {
    const result = {
        title: null,
        titleColor: null,
        openAccessText: null,
        openAccessColor: null,
        citeScore: null,
        impactFactor: null,
        coverImageUrl: null,
        pageLoaded: false
    };

    // Check if page loaded properly (not blocked)
    const errorMsg = document.querySelector('h1');
    if (errorMsg && errorMsg.textContent.includes('problem providing')) {
        result.pageLoaded = false;
        return result;
    }
    result.pageLoaded = true;

    // ── Extract Title and Color ──────────────────────────────────────────
    const titleSelectors = [
        'h1.js-title-text a.js-title-link',
        '#journal-title',
        'h1.js-title-text',
        'h1 a[usagezone="jrnl_banner"]'
    ];
    
    for (const sel of titleSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            result.title = el.textContent.trim();
            // Get color from inline style or computed style
            const style = el.getAttribute('style') || '';
            const colorMatch = style.match(/color:\\s*rgb\(([^)]+)\)/);
            if (colorMatch) {
                result.titleColor = 'rgb(' + colorMatch[1] + ')';
            } else {
                // Try computed style
                const computed = window.getComputedStyle(el);
                result.titleColor = computed.color;
            }
            break;
        }
    }

    // ── Extract Open Access Text and Color ──────────────────────────────
    const oaSelectors = [
        'span.js-open-statement-text',
        '.open-statement-text'
    ];
    
    for (const sel of oaSelectors) {
        const elements = document.querySelectorAll(sel);
        const texts = [];
        const colors = [];
        
        elements.forEach(el => {
            const text = el.textContent.trim();
            if (text) {
                texts.push(text);
                
                // Get color
                const style = el.getAttribute('style') || '';
                const colorMatch = style.match(/color:\\s*rgb\(([^)]+)\)/);
                if (colorMatch) {
                    colors.push('rgb(' + colorMatch[1] + ')');
                } else {
                    const computed = window.getComputedStyle(el);
                    colors.push(computed.color);
                }
            }
        });
        
        if (texts.length > 0) {
            result.openAccessText = texts.join(' | ');
            result.openAccessColor = colors.join(' | ');
            break;
        }
    }

    // ── Extract CiteScore ───────────────────────────────────────────────
    const csEl = document.querySelector('div.js-cite-score span.text-l');
    if (csEl) {
        result.citeScore = csEl.textContent.trim();
    }

    // ── Extract Impact Factor ───────────────────────────────────────────
    const ifEl = document.querySelector('div.js-impact-factor span.text-l');
    if (ifEl) {
        result.impactFactor = ifEl.textContent.trim();
    }

    // ── Extract Cover Image ─────────────────────────────────────────────
    const imgEl = document.querySelector('img.cover-image, img.js-cover-image');
    if (imgEl) {
        result.coverImageUrl = imgEl.src;
    }

    return result;
}
"""


async def scrape_journal(browser, url, idx, total, screenshots_dir):
    """Scrape a single journal - extract colors via JavaScript"""
    record = {
        'url': url,
        'title': None,
        'title_color_rgb': None,
        'open_access_text': None,
        'open_access_color_rgb': None,
        'cite_score': None,
        'impact_factor': None,
        'cover_image_url': None,
        'screenshot': None,
        'page_blocked': False,
        'error': None
    }

    context = None
    page = None

    try:
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        print(f"  [{idx}/{total}] Navigating: {url[:80]}...")

        # Navigate
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(4000)  # Wait for JS to render

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, f"journal_{idx:04d}.png")
        await page.screenshot(path=screenshot_path, full_page=False)
        record['screenshot'] = screenshot_path

        # Extract data via JavaScript
        data = await page.evaluate(JS_EXTRACT_COLORS)

        if not data['pageLoaded']:
            record['page_blocked'] = True
            record['error'] = 'Page blocked by site protection'
            print(f"    ⚠ BLOCKED")
        else:
            record['title'] = data['title']
            record['title_color_rgb'] = data['titleColor']
            record['open_access_text'] = data['openAccessText']
            record['open_access_color_rgb'] = data['openAccessColor']
            record['cite_score'] = data['citeScore']
            record['impact_factor'] = data['impactFactor']
            record['cover_image_url'] = data['coverImageUrl']
        
            title_display = record['title'][:50] if record['title'] else 'N/A'
            print(f"    ✓ Title: {title_display}...")
            print(f"    ✓ Title Color: {record['title_color_rgb']}")
            print(f"    ✓ OA Text: {record['open_access_text']}")
            print(f"    ✓ OA Color: {record['open_access_color_rgb']}")

    except Exception as e:
        record['error'] = str(e)
        print(f"    ✗ Error: {e}")
    finally:
        if page:
            await page.close()
        if context:
            await context.close()

    return record


async def main():
    # Read Excel
    excel_path = 'jnlactive.xlsx'
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} journals from {excel_path}\n")

    if 'Shortcut URL' not in df.columns:
        print("ERROR: 'Shortcut URL' column not found!")
        return

    # Create output folder
    screenshots_dir = 'screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)

    results = []
    total = len(df)

    print("=" * 70)
    print("EXTRACTING COLORS FROM JOURNAL WEB PAGES")
    print("=" * 70)
    print("Note: This may be blocked by site protection. Progress is saved.")
    print("=" * 70 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        try:
            for idx, row in df.iterrows():
                url = row.get('Shortcut URL')

                if pd.isna(url) or not str(url).strip():
                    print(f"[{idx+1}/{total}] Skipping: empty URL")
                    continue

                print(f"\n[{idx+1}/{total}] Processing...")

                record = await scrape_journal(
                    browser, str(url).strip(), idx + 1, total, screenshots_dir
                )

                # Add original Excel data
                record['full_title'] = row.get('Full Title', '')
                record['issn'] = row.get('ISSN', '')
                record['product_id'] = row.get('Product ID', '')

                results.append(record)

                # Save progress every 5 entries
                if len(results) % 5 == 0:
                    temp_df = pd.DataFrame(results)
                    temp_df.to_excel('journal_colors_progress.xlsx', index=False)
                    print(f"\n  >> Progress saved: {len(results)} entries")

                # Delay between requests
                await asyncio.sleep(2)

        finally:
            await browser.close()

    # Final save
    result_df = pd.DataFrame(results)
    output_path = 'journal_data_with_colors.xlsx'
    result_df.to_excel(output_path, index=False)

    # Summary
    blocked = result_df['page_blocked'].sum()
    errors = result_df['error'].notna().sum() - blocked
    success = len(result_df) - blocked - errors

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"Output file : {output_path}")
    print(f"Screenshots : {screenshots_dir}/")
    print(f"Successful  : {success}")
    print(f"Blocked     : {blocked}")
    print(f"Errors      : {errors}")
    print("=" * 70)


if __name__ == '__main__':
    asyncio.run(main())
