#!/usr/bin/env python3
"""Archive the project's explicit source catalogue; no crawling or third-party uploads.

Usage: python3 scripts/archive_research.py [--download] [--only SOURCE_ID ...]
The default copies existing downloads and rebuilds the register without networking.
--download retrieves pending public URLs. Existing successful captures are preserved.
"""
import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / 'research-dossier'
START = DOSSIER / '00 - Start Here'
CATALOGUE = ROOT / 'scripts' / 'research-sources.json'
OLD = Path('/Users/dumebi/Documents/Codex/2026-11-23/you-x20/work')

FOLDERS = [
 '01 - Group, Ownership & Funding/Parent company filings',
 '01 - Group, Ownership & Funding/Subsidiary company filings/Kensal House Nursery - 13669806',
 '01 - Group, Ownership & Funding/Investors and funding announcements',
 '01 - Group, Ownership & Funding/Acquisitions, disposals and ownership changes',
 '02 - Sites & Property/Kensal - Jaegos House and Kensal House Nursery',
 '02 - Sites & Property/Parsons Green - Jesses House and Parsons House Nursery',
 '02 - Sites & Property/East Sheen - Orlys House',
 '02 - Sites & Property/Chiswick - Olives House',
 '02 - Sites & Property/Clapham - Leos House',
 '02 - Sites & Property/Group property strategy',
 '02 - Sites & Property/Reference properties',
 '03 - Commercial Model & Marketing/Membership prices, benefits and terms',
 '03 - Commercial Model & Marketing/Nursery offer and admissions',
 '03 - Commercial Model & Marketing/Pre-launch marketing and launch chronology',
 '03 - Commercial Model & Marketing/Hospitality, activities and childcare services',
 '04 - Regulation & Operating Requirements/EYFS and space requirements',
 '04 - Regulation & Operating Requirements/Childcare registration and exemptions',
 '04 - Regulation & Operating Requirements/VAT and tax guidance',
 '05 - Comparable Operators/Storal',
 '05 - Comparable Operators/Private family clubs',
 '06 - Our Analysis & Your Project/Business model and operating economics',
 '06 - Our Analysis & Your Project/Site size and accommodation assumptions',
 '06 - Our Analysis & Your Project/Funding and entry options',
 '06 - Our Analysis & Your Project/Your brief and agreed constraints',
 '06 - Our Analysis & Your Project/Site search commission',
]

class ReadableText(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.hidden = 0
  self.parts = []
 def handle_starttag(self, tag, attrs):
  if tag in ('script', 'style', 'noscript', 'template', 'svg'):
   self.hidden += 1
  if not self.hidden and tag in ('p','div','h1','h2','h3','h4','li','br','tr','section','article'):
   self.parts.append('\n')
 def handle_endtag(self, tag):
  if tag in ('script', 'style', 'noscript', 'template', 'svg') and self.hidden:
   self.hidden -= 1
  if not self.hidden and tag in ('p','div','h1','h2','h3','h4','li','tr','section','article'):
   self.parts.append('\n')
 def handle_data(self, data):
  if not self.hidden:
   self.parts.append(data)
 def result(self):
  return '\n'.join(x for x in (re.sub(r'\s+', ' ', s).strip() for s in ''.join(self.parts).splitlines()) if x)

def safe_link(path):
 return quote(str(path).replace('\\','/'), safe='/')

def process(source, previous, download):
 row = dict(source)
 folder = DOSSIER / source['folder']
 folder.mkdir(parents=True, exist_ok=True)
 target = folder / source['filename']
 old = previous.get(source['id'], {})
 row.update({k:v for k,v in old.items() if k not in source})
 now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
 if target.exists() and old.get('status') == 'archived':
  return row
 try:
  if source.get('previous_file') and (OLD / source['previous_file']).exists():
   original = OLD / source['previous_file']
   shutil.copy2(original, target)
   row['capture_date'] = dt.datetime.fromtimestamp(original.stat().st_mtime,dt.timezone.utc).isoformat(timespec='seconds')
   row['archive_method'] = 'Copied original download from previous workspace; original file timestamp used as capture estimate'
   row['filed_at'] = now
  elif download:
   part = target.with_suffix(target.suffix+'.part')
   result = subprocess.run(['curl','--location','--fail','--silent','--show-error','--retry','1','--connect-timeout','12','--max-time','45','--user-agent','Mozilla/5.0 (compatible; ResearchArchive/1.0)','--output',str(part),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}',source['url']],capture_output=True,text=True,timeout=105)
   fields = result.stdout.splitlines()
   row['last_attempt'] = now
   row['http_status'] = fields[0] if fields else ''
   row['resolved_url'] = fields[1] if len(fields)>1 else ''
   row['content_type'] = fields[2] if len(fields)>2 else ''
   if result.returncode:
    part.unlink(missing_ok=True)
    raise ValueError((result.stderr or 'Download failed').strip()[:450])
   data = part.read_bytes()
   if target.suffix == '.pdf' and not data.startswith(b'%PDF-'):
    part.unlink(missing_ok=True)
    raise ValueError('Response was not a PDF; no error/interstitial page retained as evidence')
   if target.suffix == '.html':
    body = data.decode('utf-8', errors='replace')
    parser = ReadableText(); parser.feed(body)
    readable = parser.result()
    low = readable.lower()
    title = re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
    title = html.unescape(title.group(1)).strip() if title else ''
    challenge = any(x in (title+' '+readable[:500]).lower() for x in ['just a moment','access denied','enable javascript and cookies','security verification','request blocked','403 forbidden'])
    if challenge or len(readable) < 100:
     part.unlink(missing_ok=True)
     raise ValueError('Page returned an access challenge or insufficient readable content; not archived as source evidence')
    row['captured_title'] = title
   part.replace(target)
   row['capture_date'] = now
   row['archive_method'] = 'Direct public URL download'
  else:
   row['status'] = old.get('status','pending_download')
   return row
  data = target.read_bytes()
  if target.suffix == '.pdf' and not data.startswith(b'%PDF-'):
   raise ValueError('PDF signature validation failed')
  row['local_file'] = str(target.relative_to(DOSSIER))
  row['sha256'] = hashlib.sha256(data).hexdigest()
  row['bytes'] = len(data)
  if target.suffix == '.html':
   parser = ReadableText(); parser.feed(data.decode('utf-8',errors='replace'))
   text_file = target.with_suffix('.txt')
   text_file.write_text('Title: '+source['title']+'\nSource: '+source['url']+'\nCaptured: '+row['capture_date']+'\n\n'+parser.result()+'\n')
   row['readable_file'] = str(text_file.relative_to(DOSSIER))
   row['offline_limitations'] = 'HTML response and readable text saved; images/styles/scripts and linked pages are not bundled. Text extraction may omit browser-rendered content.'
  elif target.suffix == '.pdf':
   text_target = target.with_suffix('.txt')
   oldstem = Path(source.get('previous_file','')).stem
   ocr = OLD / (oldstem+'.ocr.txt')
   extracted = OLD / (oldstem+'.txt')
   if oldstem and ocr.exists():
    text_target.write_text('SEARCH AID: OCR may contain errors; verify against original PDF.\n\n'+ocr.read_text())
   elif oldstem and extracted.exists() and len(extracted.read_text().strip()) > 300:
    text_target.write_text('SEARCH AID: extracted text; original PDF is authoritative.\n\n'+extracted.read_text())
   else:
    try:
     import pdfplumber
     with pdfplumber.open(target) as pdf:
      row['page_count'] = len(pdf.pages)
      text = '\n\n'.join(f'--- PDF page {i+1} ---\n'+(p.extract_text() or '') for i,p in enumerate(pdf.pages))
     if len(re.sub(r'--- PDF page \d+ ---','',text).strip()) > 100:
      text_target.write_text('SEARCH AID: extracted text; original PDF is authoritative.\n\n'+text+'\n')
    except ImportError:
     pass
   if text_target.exists():
    row['readable_file'] = str(text_target.relative_to(DOSSIER))
  row['status'] = 'archived'
  row.pop('error',None)
 except Exception as exc:
  row['status'] = 'access_gap'
  row['error'] = str(exc)
 return row

def write_indexes(rows):
 START.mkdir(parents=True,exist_ok=True)
 (START/'source-register.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
 fields = ['id','title','publisher','evidence_type','publication_date','date_note','company_number','topics','supports','relevant_pages','status','local_file','readable_file','url','capture_date','archive_method','offline_limitations','error','sha256','bytes']
 with (START/'source-register.csv').open('w',newline='') as f:
  writer = csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
 archived = sum(r.get('status')=='archived' for r in rows)
 lines = ['# Source register','',f'Updated {dt.datetime.now(dt.timezone.utc).date()}. {archived} of {len(rows)} catalogue entries archived.','',
 'Original files are the evidence. Readable text is a search aid, particularly where OCR was used. Web captures are dated snapshots, not historical archives of earlier page versions.','',
 'Machine-readable registers: [CSV](source-register.csv) · [JSON](source-register.json).','']
 for group in FOLDERS:
  selected = [r for r in rows if r['folder']==group]
  if not selected: continue
  lines += ['## '+group,'']
  for r in selected:
   links = [f"[Original URL]({r['url']})"]
   if r.get('status')=='archived':
    links.insert(0, f"[Saved source](../{safe_link(r['local_file'])})")
    if r.get('readable_file'): links.append(f"[Readable text](../{safe_link(r['readable_file'])})")
   lines += [f"- **{r['id']} — {r['title']}** ({r['evidence_type']}; date: {r.get('publication_date') or 'not established'}; {r.get('status')}).", '  '+' · '.join(links), '  '+r['supports']]
   if r.get('relevant_pages'): lines.append('  Relevant pages: '+r['relevant_pages'])
   for extract in r.get('page_extracts',[]):
    lines.append(f"  [Saved extract: {extract['title']}](../{safe_link(extract['local_file'])}) — {extract['page_reference']}; derivative of {r['id']}, not a separate source.")
   if r.get('error'): lines.append('  Access gap: '+r['error'])
  lines += ['']
 (START/'Source register.md').write_text('\n'.join(lines)+'\n')
 gaplines = ['# Open questions and evidence gaps','','## Archive access gaps','']
 gaps = [r for r in rows if r.get('status')!='archived']
 if not gaps: gaplines.append('No outstanding access gaps in the current source catalogue.')
 for r in gaps:
  gaplines.append(f"- **{r['id']} — {r['title']}**: {r.get('error',r.get('status'))}. [Original URL]({r['url']})")
 gaplines += ['', '## Research questions that remain unresolved','',
 '- Area evidence is partly resolved at both existing sites: LC02 gives Parsons nursery room areas and Jesse’s club NIA; original Kensal planning KP02 gives nursery and club room annotations, and KP06 gives a combined GIA entry with a material form error. Full nursery GIA, comparable club/nursery/shared splits, as-built layouts and the extent of headline marketing areas remain unverified. Keep the sites and measurement bases separate.',
 '- Confirmed day-nursery provision and capacity in future clubs. A crèche or kids club does not establish a full-day nursery operation.',
 '- Original pre-launch marketing spend, paid channels, leads, conversion rates and acquisition costs. Public posts establish examples, not a complete marketing ledger.',
 '- Complete opening sources and uses of funds, original loan-note coupon/conversion terms, and the fully diluted economic ownership waterfall.',
 '- Site-level club operating results and cash flow; parent-only accounts and nursery-company accounts do not constitute consolidated or combined site results.',
 '- Competitor gaps: current b_together club subscription, Mumadoo physical opening date, and delivery of The JJ Club physical flagship remain unconfirmed. Advertised membership offers do not establish profitability, demand or nursery capacity.',
 '- Property-specific feasibility, costs, funding terms and demand for the user’s proposed first location. No approved design, lending offer or property shortlist exists.',
 '- The 2026 nursery ownership change needs a dedicated review before using it to draw conclusions about the original model or current strategy.',
 '', 'Coverage: this backfill uses the retained downloads and identifiable core URLs from the conversation. It is not a reconstruction of every search result or every historical version viewed.']
 (START/'Open questions and evidence gaps.md').write_text('\n'.join(gaplines)+'\n')
 for group in FOLDERS:
  folder = DOSSIER/group; folder.mkdir(parents=True,exist_ok=True)
  entries = [r for r in rows if r['folder']==group]
  text = ['# '+folder.name,'','[Full source register]('+safe_link(Path(__import__('os').path.relpath(START/'Source register.md',folder)))+')','']
  for r in entries:
   if r.get('status')=='archived':
    text.append(f"- [{r['title']}]({safe_link(r['filename'])}) — {r['id']}; {r['supports']}")
   else: text.append(f"- {r['id']} — {r['title']}: {r.get('status')}; see the source register.")
  other_files = sorted(p for p in folder.iterdir() if p.is_file() and (p.suffix=='.md' or (group.startswith('06 - ') and p.suffix=='.txt')) and p.name!='README.md')
  for p in other_files:
   label = 'Search prompt' if 'prompt' in p.stem.lower() else 'Working note'
   text.append(f'- [{label}: {p.stem}]({safe_link(p.name)}) — project instruction/analysis, not an original external source.')
  if not entries and not other_files: text.append('Folder reserved for this topic. No source or analysis has been filed here yet.')
  if 'Kensal - ' in group:
   rel = Path(__import__('os').path.relpath(DOSSIER/'01 - Group, Ownership & Funding/Subsidiary company filings/Kensal House Nursery - 13669806',folder))
   text += ['',f'Nursery-company accounts: [Kensal House Nursery Limited, 13669806]({safe_link(rel)}/README.md).']
  if group.startswith('02 - Sites'):
   text += ['', 'For executed group lease schedules, see CH12 in the [source register]('+safe_link(Path(__import__('os').path.relpath(START/'Source register.md',folder)))+').']
  (folder/'README.md').write_text('\n'.join(text)+'\n')
 for topic in dict.fromkeys(f.split('/')[0] for f in FOLDERS):
  subfolders = [f for f in FOLDERS if f.startswith(topic+'/')]
  topiclines = ['# '+topic,'','[Dossier home](../README.md)','']
  for f in subfolders:
   count=sum(r['folder']==f and r.get('status')=='archived' for r in rows)
   relative=f[len(topic)+1:]
   topiclines.append(f'- [{relative}]({safe_link(relative)}/README.md) — {count} original sources archived.')
  (DOSSIER/topic/'README.md').write_text('\n'.join(topiclines)+'\n')
 home=['# OurHouse and nursery-club research dossier','',
  f'Updated {dt.datetime.now(dt.timezone.utc).date()}: **{archived} of {len(rows)} catalogued sources archived**, with {len(rows)-archived} access gaps/pending entries.','',
  '[Research guide](00%20-%20Start%20Here/Research%20guide.md) · [Source register](00%20-%20Start%20Here/Source%20register.md) · [Sortable CSV](00%20-%20Start%20Here/source-register.csv) · [Evidence gaps](00%20-%20Start%20Here/Open%20questions%20and%20evidence%20gaps.md)','',
  '## Browse by topic','']
 for topic in dict.fromkeys(f.split('/')[0] for f in FOLDERS):
  home.append(f'- [{topic}]({safe_link(topic)}/README.md)')
 home += ['', '## Quick links','',
  '- [Your agreed project brief](06%20-%20Our%20Analysis%20%26%20Your%20Project/Your%20brief%20and%20agreed%20constraints/Project%20brief.md)',
  '- [Research findings retained from the conversation](06%20-%20Our%20Analysis%20%26%20Your%20Project/Business%20model%20and%20operating%20economics/Research%20findings%20retained%20from%20conversation.md)',
  '- [Preliminary space brief and illustrative allocation](06%20-%20Our%20Analysis%20%26%20Your%20Project/Site%20size%20and%20accommodation%20assumptions/Preliminary%20space%20brief.md)',
  '', 'Original sources and working assumptions are kept separately. Unfilled folders are explicitly marked. Historical publicity and current captures are not interchangeable. Core sources used in future research must be filed and registered as part of that work; see the project AGENTS.md.',
  '', 'Webpage captures include HTML and readable text, but do not bundle external images, styles, scripts or linked pages. Some interactive content may be available only in the HTML or require a browser.']
 (DOSSIER/'README.md').write_text('\n'.join(home)+'\n')

def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--download',action='store_true'); parser.add_argument('--only',nargs='*')
 args=parser.parse_args()
 catalogue=json.loads(CATALOGUE.read_text())
 register=START/'source-register.json'
 previous={r['id']:r for r in json.loads(register.read_text())} if register.exists() else {}
 rows={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  futures={pool.submit(process,s,previous,args.download and (not args.only or s['id'] in args.only)):s['id'] for s in catalogue}
  for future in concurrent.futures.as_completed(futures):
   r=future.result(); rows[r['id']]=r
   print(r['id']+': '+r.get('status','unknown'),flush=True)
 ordered=[rows[s['id']] for s in catalogue]
 write_indexes(ordered)
 print(json.dumps({'catalogued':len(ordered),'archived':sum(r.get('status')=='archived' for r in ordered),'gaps':sum(r.get('status')!='archived' for r in ordered)}),flush=True)

if __name__=='__main__': main()
