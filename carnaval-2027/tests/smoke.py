"""Browser smoke test against local or published /carnaval-2027/. Requires playwright.
Screenshots and detailed logs stay outside the public repository unless --out is given.
"""
import argparse,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url',default='http://127.0.0.1:8765/carnaval-2027/');ap.add_argument('--out',type=Path,default=Path(tempfile.gettempdir())/'rota27-qa');a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True)
 passed=[];errors=[]
 with sync_playwright() as pw:
  try:b=pw.chromium.launch(channel='msedge',headless=True)
  except Exception:b=pw.chromium.launch(headless=True)
  context=b.new_context(viewport={'width':1440,'height':1000},locale='pt-BR',accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(a.url,wait_until='networkidle');expect(page.locator('.offer').first).to_be_visible();passed.append('loading and subfolder assets')
  for n in [2,3,5,6]:
   page.locator(f'#persons button[data-n="{n}"]').click();expect(page.locator('.offer').first).to_be_visible();expect(page.locator(f'#persons button[data-n="{n}"]')).to_have_attribute('aria-pressed','true')
  passed.append('all four group filters')
  page.locator('#persons button[data-n="2"]').click()
  dests=page.locator('#destination option').evaluate_all('(els)=>els.map(e=>e.value).filter(x=>x!=="all")');assert len(dests)==12
  for dest in dests:
   page.locator('#destination').select_option(dest);assert page.locator('.offer').count()>0,dest
  passed.append('all twelve destination filters have two-adult results')
  page.locator('#destination').select_option('all');page.locator('#travel').select_option('Ônibus');assert page.locator('.offer').count()>0;expect(page.locator('.offer-price b').first).to_have_text('—');page.locator('#travel').select_option('Avião');passed.append('transport filter and unknown bus price')
  page.locator('#checkout').fill('2027-02-11');page.locator('#checkout').dispatch_event('change');expect(page.locator('#dateWarning')).to_be_visible();expect(page.locator('.offer-price b').first).to_have_text('—');expect(page.locator('#periodNights')).to_contain_text('6 noites');page.locator('#checkout').fill('2027-02-10');page.locator('#checkout').dispatch_event('change');passed.append('date changes invalidate quotes and recalculate nights')
  page.locator('#budget').fill('1');page.locator('#withinBudget').check();assert page.locator('.offer').count()==0;page.locator('#budget').fill('');assert page.locator('.offer').count()>0;passed.append('budget updates, no rigid default and empty budget reset')
  page.locator('.advanced summary').click();page.locator('#privacy').select_option('private');assert page.locator('.offer').count()>0;page.locator('#bathroom').select_option('private');assert page.locator('.offer').count()>0;page.locator('#privacy').select_option('all');page.locator('#bathroom').select_option('all');passed.append('privacy and bathroom reactive filters')
  page.locator('#settingsBtn').click();page.locator('#food').fill('125');page.locator('[data-weight="cost"]').fill('50');expect(page.locator('#foodDisplay')).to_contain_text('125');page.locator('#sort').select_option('ranking');passed.append('manual daily costs and ranking weights')
  page.locator('.offer-check').nth(0).check();page.locator('.offer-check').nth(1).check();page.locator('.offer-check').nth(2).check();expect(page.locator('#navCount')).to_have_text('3');page.locator('.offer-check').nth(3).click();expect(page.locator('#navCount')).to_have_text('3');page.locator('.nav [data-view="compare"]').click();assert page.locator('.compare-card').count()==3;passed.append('three comparisons and selection limit')
  for view in ['destinations','history','pending','database']:
   page.locator(f'.nav [data-view="{view}"]').click();assert len(page.locator('#dynamic').inner_text())>80
  passed.append('all six views navigate')
  page.locator('#baseSearch').fill('confirmação');page.locator('#entity').select_option('events');page.locator('#baseSearch').fill('BaianaSystem');assert page.locator('.rawtable tbody tr').count()>0;passed.append('searchable event evidence and sources')
  with page.expect_download() as d:page.locator('#exportJson').click()
  exported=a.out/'export.json';d.value.save_as(exported);content=json.loads(exported.read_text(encoding='utf-8'));assert content['schemaVersion']==1 and len(content['database']['destinations'])==12;passed.append('JSON export of complete normalized data')
  with page.expect_download() as d:page.locator('#exportCsv').click()
  assert d.value.suggested_filename.endswith('.csv');passed.append('CSV export')
  page.locator('#manualBtn').click();form=page.locator('#manualForm');form.locator('[name="name"]').fill('Teste local <img src=x onerror=alert(1)>');form.locator('[name="destinationId"]').select_option('rio');form.locator('[name="hotel"]').fill('2000');form.locator('[name="ticket"]').fill('3000');form.locator('[name="url"]').fill('https://www.booking.com/');form.locator('button.primary').click();expect(page.locator('#manualDialog')).not_to_be_visible();assert page.locator('.details').inner_text().find('Teste local <img')>=0;assert page.locator('.details img').count()==0;passed.append('manual quote and safe text rendering')
  page.reload(wait_until='networkidle');expect(page.locator('#destination')).to_have_value('rio');expect(page.locator('#food')).to_have_value('125');assert page.evaluate('JSON.parse(localStorage.getItem("rota27-v1")).manual.length')==1;passed.append('local preferences and manual persistence')
  # Import a new local record and reject invalid input without changing public data.
  saved=page.evaluate('JSON.parse(localStorage.getItem("rota27-v1"))');record=saved['manual'][0];record['id']='manual_import_smoke';record['name']='Importado';payload=json.dumps({'schemaVersion':1,'manual':[record]})
  page.locator('#importFile').set_input_files({'name':'local.json','mimeType':'application/json','buffer':payload.encode()});page.wait_for_timeout(200);assert page.evaluate('JSON.parse(localStorage.getItem("rota27-v1")).manual.length')==2
  page.locator('#importFile').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"schemaVersion":99}'});page.wait_for_timeout(200);assert page.evaluate('JSON.parse(localStorage.getItem("rota27-v1")).manual.length')==2;passed.append('JSON import and invalid input guard')
  page.locator('#resetBtn').click();page.screenshot(path=str(a.out/'desktop.png'),full_page=True)
  for width,height in [(390,844),(768,1024)]:
   page.set_viewport_size({'width':width,'height':height});assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),f'overflow {width}';page.locator('.nav [data-view="destinations"]').click();assert page.locator('.destination-block').count()==12;page.screenshot(path=str(a.out/f'mobile-{width}.png'),full_page=True);page.locator('.nav [data-view="dashboard"]').click()
  passed.append('responsive mobile/tablet without horizontal body overflow')
  anchors=page.locator('a[target="_blank"]').evaluate_all('(els)=>els.map(a=>({href:a.href,rel:a.rel}))');assert all(x['href'].startswith('https://') and 'noopener' in x['rel'] for x in anchors);passed.append('safe external links')
  assert not errors,errors;passed.append('no browser runtime errors');context.close();b.close()
 result={'passed':passed,'count':len(passed),'runtimeErrors':errors};(a.out/'smoke-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
