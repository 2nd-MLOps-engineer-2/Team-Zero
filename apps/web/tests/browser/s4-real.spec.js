import { test, expect } from '@playwright/test';
import fs from 'node:fs/promises';
const api=process.env.S4_API_BASE_URL;
test.skip(!api,'Set S4_API_BASE_URL to the locally verified B 1.1 + C service.');
const ready=page=>expect(page.locator('#status')).toContainText('조회 완료');
async function samsung(page){await page.goto('http://127.0.0.1:4175');await ready(page);await page.selectOption('[name=stock_cd]','005930');await ready(page);}
test('S4 actual B/C values, provenance, quality and server chart export',async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await samsung(page);
  await expect(page.locator('.metric').nth(0)).toContainText('333,605,938,000,000 원');
  await expect(page.locator('.metric').nth(1)).toContainText('43,601,051,000,000 원');
  await expect(page.locator('.metric').nth(2)).toContainText('45,206,805,000,000 원');
  await expect(page.locator('.metric').nth(3)).toContainText('85,315,148,000,000 원');
  await expect(page.locator('#evidence')).toContainText('실적 개선·시장 대비 강세 동행');
  await expect(page.locator('#evidence')).toContainText('원본 파일 미확보');
  await expect(page.locator('#quality')).toContainText('전역 재무제표 이슈');
  const download=page.waitForEvent('download');await page.click('#server-export');
  const file=await download;const text=await fs.readFile(await file.path(),'utf8');
  expect(text.charCodeAt(0)).toBe(0xfeff);
  expect(text).toContain('100.00000000,100.00000000,2026-06-01');
  expect(text).toContain('93.80281690,96.45099552,2026-06-01');
  await page.screenshot({path:'test-results/s4-actual-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/s4-actual-mobile.png',fullPage:true});
  expect(errors).toEqual([]);
});
test('S4 weekend effective date, PIT same-day exclusion, missing investor and empty financials',async({page,request})=>{
  await samsung(page);
  await page.fill('[name=as_of]','2026-06-06');await page.locator('[name=as_of]').blur();await ready(page);
  await expect(page.locator('#status')).toContainText('실제 관측 2026-06-05');
  await page.fill('[name=as_of]','2026-06-30');await page.locator('[name=as_of]').blur();await ready(page);
  await page.fill('[name=start]','2026-06-06');await page.locator('[name=start]').blur();await ready(page);
  await expect(page.locator('#detail')).toContainText('2026-06-08 = 100');
  const sameDay=await request.get(`${api}/stocks/005930/financials?year=2025&report_code=11011&fs_div=CFS&as_of=2026-03-10`);
  expect((await sameDay.json()).data).toEqual([]);
  await page.selectOption('[name=basis]','OFS');await ready(page);
  await expect(page.locator('.metric').first()).toContainText('보고서 없음');
  await page.selectOption('[name=stock_cd]','247540');await ready(page);
  await page.fill('[name=start]','2026-04-16');await page.locator('[name=start]').blur();await ready(page);
  await page.fill('[name=as_of]','2026-04-16');await page.locator('[name=as_of]').blur();await ready(page);
  await page.getByText('차트 원값 · 재무 보고서 확인',{exact:true}).click();
  await expect(page.locator('#detail')).toContainText('PRICE_ONLY');
  await expect(page.locator('#detail')).toContainText('검토 대기');
  const missing=await request.get(`${api}/stocks/247540/daily?start=2026-04-16&end=2026-04-16`);
  const row=(await missing.json()).data[0];expect(row.frgn_net_buy_qty).toBeNull();expect(row.close_prc).not.toBeNull();
  expect((await request.get(`${api}/stocks/999999/daily`)).status()).toBe(404);
  expect((await request.get(`${api}/stocks/005930/daily?start=2026-02-30`)).status()).toBe(422);
});
test('S4 missing C still renders original amounts and reports 409 without fabricated analysis',async({page})=>{
  test.skip(!process.env.S4_NO_C_API_URL,'Optional real service without C artifact');
  await page.route(`${api}/**`,async route=>{
    const response=await route.fetch({url:route.request().url().replace(api,process.env.S4_NO_C_API_URL)});
    await route.fulfill({response});
  });
  await samsung(page);
  await expect(page.locator('.metric').first()).toContainText('333,605,938,000,000 원');
  await expect(page.locator('#evidence')).toContainText('C 분석 미연결');
  await expect(page.locator('#evidence')).toContainText('PENDING_C_DELIVERY');
  await page.selectOption('#csv-kind','g_stock_daily_analysis');await page.click('#server-export');
  await expect(page.locator('#export-status')).toContainText('ANALYSIS_NOT_AVAILABLE (409)');
});
test('S4 small real API pages are fully assembled without resetting the price baseline',async({page,request})=>{
  await page.route(`${api}/**`,async route=>{
    const url=new URL(route.request().url());
    if(url.searchParams.has('limit'))url.searchParams.set('limit',url.pathname.endsWith('/quality')?'50':'5');
    const response=await route.fetch({url:url.toString()});await route.fulfill({response});
  });
  await samsung(page);
  const response=await request.get(`${api}/stocks/005930/daily?start=2026-06-01&end=2026-06-30`);
  const expected=await response.json();
  await expect(page.locator('#status')).toContainText(`일별 ${expected.meta.total}개 관측`);
  await expect(page.locator('[name=stock_cd] option')).toHaveCount(20);
  await expect(page.locator('#detail')).toContainText('2026-06-01 = 100');
  await page.getByText('차트 원값 · 재무 보고서 확인',{exact:true}).click();
  await expect(page.locator('#detail')).toContainText('93.80281690');
  const quality=await request.get(`${api}/stocks/005930/quality?start=2026-06-01&end=2026-06-30`);
  await expect(page.locator('#quality')).toContainText(`기업·보고서 이슈 (${(await quality.json()).meta.total})`);
});
