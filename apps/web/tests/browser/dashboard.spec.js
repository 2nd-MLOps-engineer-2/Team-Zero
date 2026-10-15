import { test, expect } from '@playwright/test';
import fixture from '../../src/fixtures/sample.json' with {type:'json'};
import fs from 'node:fs/promises';

const ready=async page=>await expect(page.locator('#status')).toContainText('조회 완료');
test('desktop shows cards, charts, evidence and source states',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await ready(page);
 await expect(page.locator('#comparison tbody tr')).toHaveCount(20);
 await expect(page.locator('.metric').first()).toContainText('11,200,000,000,000 원');
 await expect(page.locator('svg')).toHaveCount(6);
 await expect(page.locator('#evidence')).toContainText('미확보');
 await expect(page.locator('#evidence')).toContainText('격리');
 await page.screenshot({path:'test-results/desktop.png',fullPage:true});
 expect(errors).toEqual([]);
});
test('filters update market, stock, reporting and date results',async({page})=>{
 await page.goto('/');await ready(page);
 await page.selectOption('[name=market]','KOSDAQ');await ready(page);
 await expect(page.locator('#comparison tbody tr')).toHaveCount(6);
 await page.selectOption('[name=report]','11012');await ready(page);
 await expect(page.locator('.metric').first()).toContainText('보고서 없음');
 await page.fill('[name=start]','2026-06-15');await page.locator('[name=start]').blur();await ready(page);
 await expect(page.locator('#status')).toContainText('일별 3개 관측');
});
test('NULL and actual zero remain distinct when switching companies',async({page})=>{
 await page.goto('/');await ready(page);
 await page.selectOption('[name=stock_cd]',fixture.stocks[2].stock_cd);await ready(page);
 await expect(page.locator('.metric').nth(1)).toContainText('0 원');
 await page.selectOption('[name=stock_cd]',fixture.stocks[3].stock_cd);await ready(page);
 await expect(page.locator('.metric').nth(3)).toContainText('미제공 (NULL)');
 await expect(page.locator('#evidence')).toContainText('계산 불가');
});
test('loading, error, retry, empty and recovery clear stale export',async({page})=>{
 await page.goto('/');await ready(page);
 await page.selectOption('[name=scenario]','error');
 await expect(page.locator('#export')).toBeDisabled();
 await expect(page.getByRole('alert')).toContainText('샘플 응답 오류');
 await page.getByRole('button',{name:'다시 시도',exact:true}).click();
 await expect(page.getByRole('alert')).toBeVisible();
 await page.selectOption('[name=scenario]','empty');await ready(page);
 await expect(page.locator('#comparison')).toContainText('조회 결과가 없습니다');
 await expect(page.locator('#export')).toBeDisabled();
 await page.selectOption('[name=scenario]','normal');await ready(page);
 await expect(page.locator('#export')).toBeEnabled();
});
test('CSV contains the same exact financial value and NULL provenance',async({page})=>{
 await page.goto('/');await ready(page);
 const pending=page.waitForEvent('download');await page.locator('#export').click();
 const download=await pending;const text=await fs.readFile(await download.path(),'utf8');
 expect(download.suggestedFilename()).toContain('SAMPLE-000660-2026-06-30');
 expect(text).toContain('"rev_ytd_amt","11200000000000","KRW"');
 expect(text).toContain('"frgn_net_buy_qty","NULL","shares"');
 expect(text).toContain('synthetic-ui-v1');
});
test('mobile layout has no document overflow and remains usable',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await ready(page);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('#raw-values summary').click();await expect(page.locator('#raw-values')).toHaveAttribute('open','');
 await page.screenshot({path:'test-results/mobile.png',fullPage:true});
});
test('invalid date range clears previous results and blocks download',async({page})=>{
 await page.goto('/');await ready(page);
 await page.fill('[name=as_of]','2026-05-20');await page.locator('[name=as_of]').blur();
 await expect(page.locator('#status')).toContainText('시작일은 기준일보다');
 await expect(page.locator('#export')).toBeDisabled();await expect(page.locator('#results')).toBeEmpty();
});
test('rapid company changes display only the final selection',async({page})=>{
 await page.goto('/');await ready(page);
 await page.selectOption('[name=stock_cd]',fixture.stocks[1].stock_cd);
 await page.selectOption('[name=stock_cd]',fixture.stocks[2].stock_cd);await ready(page);
 await expect(page.locator('#detail h2')).toContainText(fixture.stocks[2].stock_nm);
 await expect(page.locator('.metric').nth(1)).toContainText('0 원');
});
test('API mode uses supplied responses, escapes markup, and never falls back on 500',async({page})=>{
 let fail=false;
 await page.route('**/api/**',async route=>{
  if(fail){await route.fulfill({status:500,body:'failure'});return;}
  const url=new URL(route.request().url());let rows;
  if(url.pathname==='/api/stocks')rows=fixture.stocks;
  else if(url.pathname.endsWith('/compare'))rows=fixture.compare;
  else if(url.pathname.endsWith('/daily'))rows=fixture.daily['000660'];
  else if(url.pathname.endsWith('/financials'))rows=fixture.financials['000660'];
  else rows=[{...fixture.evidence['000660'],classification:'<img src=x onerror=alert(1)>'}];
  await route.fulfill({json:{meta:{...fixture.meta,synthetic:false,calc_version:'mock-contract-test'},data:rows}});
 });
 await page.goto('http://127.0.0.1:4174');await ready(page);
 await expect(page.locator('#status')).toContainText('API 응답');
 await expect(page.locator('#evidence h3').first()).toHaveText('<img src=x onerror=alert(1)>');
 await expect(page.locator('#evidence img')).toHaveCount(0);
 fail=true;await page.locator('#submit').click();
 await expect(page.getByRole('alert')).toContainText('500');await expect(page.locator('#export')).toBeDisabled();
 await expect(page.locator('.metric')).toHaveCount(0);
});
test('G03 scatter supports keyboard selection and distinguishes joint improvement',async({page})=>{
 await page.goto('/');await ready(page);
 const point=page.locator('.scatter circle').first();await point.focus();await page.keyboard.press('Enter');await ready(page);
 await expect(page.locator('#detail h2')).toContainText('SK하이닉스');
 await expect(page.locator('#evidence')).toContainText('복합 동반 개선:');
 await expect(page.getByRole('heading',{name:'20관측 수급 비율'})).toBeVisible();
 await expect(page.locator('.scatter')).toContainText('판단 불가 5개');
});
test('G03 price baseline follows requested range without altering flow ratios',async({page})=>{
 await page.goto('/');await ready(page);
 await page.fill('[name=start]','2026-06-12');await page.locator('[name=start]').blur();await ready(page);
 await expect(page.locator('#detail')).toContainText('2026-06-15 = 100');
 await page.locator('#raw-values summary').click();
 await expect(page.locator('#raw-values tbody tr').first()).toContainText('1.4 %');
});

test('report charts support keyboard observations, series toggles and period selection',async({page})=>{
 await page.goto('/');await ready(page);
 await expect(page.locator('#company-summary')).toContainText('SK하이닉스');
 const price=page.locator('#price-report'),slider=price.locator('input[type=range]');
 await slider.focus();await page.keyboard.press('Home');
 await expect(price.locator('.chart-readout')).toContainText('2026-06-01');
 const market=price.locator('[data-series-toggle="1"]');await market.click();
 await expect(market).toHaveAttribute('aria-pressed','false');
 await expect(price.locator('[data-series="1"]')).toBeHidden();
 await market.click();await expect(price.locator('[data-series="1"]')).toBeVisible();
 expect(await page.locator('#financial-report rect').count()).toBeGreaterThan(0);
 expect(await page.locator('#flow-report rect').count()).toBeGreaterThan(0);
 await price.getByRole('button',{name:'3M',exact:true}).click();await ready(page);
 await expect(page.locator('[name=start]')).toHaveValue('2026-04-02');
 await expect(price.getByRole('button',{name:'3M',exact:true})).toHaveAttribute('aria-pressed','true');
 await page.locator('.report-sidebar a[href="#price-report"]').click();
 await expect(price).toBeInViewport();
 await page.screenshot({path:'test-results/report-chart.png'});
});
