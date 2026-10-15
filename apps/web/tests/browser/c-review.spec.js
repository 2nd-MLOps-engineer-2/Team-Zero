import { test, expect } from '@playwright/test';
import fs from 'node:fs/promises';

test('C actual Gold response values agree with rendered amounts, ratios and export',async({page})=>{
 test.skip(!process.env.C_REVIEW_BUNDLE,'Optional C review bundle; see scripts/prepare-c-review.py');
 const bundle=JSON.parse(await fs.readFile(process.env.C_REVIEW_BUNDLE,'utf8'));
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  const kind=path==='/api/stocks'?'stocks':path.endsWith('/compare')?'compare':path.endsWith('/daily')?'daily':path.endsWith('/financials')?'financials':'evidence';
  await route.fulfill({json:{meta:bundle.meta,data:bundle[kind]}});
 });
 await page.goto('http://127.0.0.1:4174');
 await expect(page.locator('#status')).toContainText('조회 완료');
 await expect(page.locator('.metric').first()).toContainText('333,605,938,000,000 원');
 await expect(page.locator('#evidence')).toContainText('10.88 %');
 await expect(page.locator('#evidence')).toContainText('32.77 %p');
 await expect(page.locator('#evidence')).toContainText('조건 미충족');
 await page.locator('#raw-values summary').click();
 await expect(page.locator('#raw-values')).toContainText('-6.46 %');
 const pending=page.waitForEvent('download');await page.locator('#export').click();
 const file=await pending;const csv=await fs.readFile(await file.path(),'utf8');
 expect(csv).toContain('333605938000000');expect(csv).toContain('0.32769823');expect(csv).toContain('c-gold-0.1.0');
 expect(file.suggestedFilename()).not.toContain('SAMPLE');
 await page.screenshot({path:'test-results/c-actual-review.png',fullPage:true});
});
