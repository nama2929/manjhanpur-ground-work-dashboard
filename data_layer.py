"""Google Sheets LIVE reader and source-respecting normalizer.
No writes; does not guess missing dates or fabricate translations.
"""
import datetime as dt
import io
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import urlsplit
from config import COORDINATORS, TABS

GOOGLE_SCOPES=['https://www.googleapis.com/auth/spreadsheets.readonly']


def cell(row,i):
    if i is None or i < 0 or i>=len(row): return ''
    return str(row[i] if row[i] is not None else '').strip()


def clean_tab(s):
    return re.sub(r'[^\w\u0900-\u097f]+','',str(s).lower().strip())


def match_tabs(names):
    result={}
    for k,meta in TABS.items():
        aliases={clean_tab(v) for v in meta['aliases']}
        result[k]=next((n for n in names if clean_tab(n) in aliases),None)
    return result


def parse_date(value):
    s=str(value or '').strip()
    if not s:return None
    if re.fullmatch(r'\d{5}(?:\.0+)?',s):
        try:return (dt.datetime(1899,12,30)+dt.timedelta(days=float(s))).date()
        except (ValueError,OverflowError):pass
    for fmt in ('%Y-%m-%d','%d.%m.%Y','%d/%m/%Y','%d-%m-%Y','%m/%d/%Y','%d/%m/%y','%Y/%m/%d','%d %b %Y','%d %B %Y','%d.%m.%y'):
        try:return dt.datetime.strptime(s.split(' ')[0] if fmt in ('%Y-%m-%d','%d.%m.%Y','%d/%m/%Y','%d-%m-%Y','%m/%d/%Y') else s,fmt).date()
        except ValueError:pass
    return None


def to_int(s):
    try:return max(0,int(float(str(s).replace(',','').strip() or '0')))
    except (TypeError,ValueError,OverflowError):return 0


def header_location(rows,kind):
    marker={'daily':('दिनांक','बूथ'), 'registration':('कार्यकर्ता का पूरा नाम','बूथ संख्या'),
            'whatsapp':('ग्रुप में','WhatsApp ग्रुप'), 'actions':('पंचायत/गांव','एक्शनेबल बिंदु'),
            'booth':('कार्यकर्ता का पूरा नाम','बूथ संख्या'), 'social':('सोशल मीडिया प्लेटफॉर्म','प्रोफाइल लिंक')}[kind]
    for i,row in enumerate(rows[:8]):
        txt='|'.join(map(str,row))
        if any(m in txt for m in marker) and ('क्रम' in txt or 'क्र.' in txt):return i
    return 0 if kind in ('daily','whatsapp','actions') else 1


def extra_date_col(headers,kind):
    # Only use an explicit date column, never row creation time or today's date.
    for idx,h in enumerate(headers):
        s=str(h).strip().lower()
        if idx==0:continue
        if ('दिनांक' in s or 'तारीख' in s or 'entry date' in s or 'date'==s or 'entry_date' in s):
            # dates in daily & registration already have well-defined positions
            return idx
    return None


def normalize_rows(kind,rows,worker,actual_tab):
    if not rows:return [], {'source_rows':0,'eligible':0,'undated':0,'incomplete':0}
    idx=header_location(rows,kind)
    headers=rows[idx]
    date_extra=extra_date_col(headers,kind)
    shifted=kind=='actions' and len(headers)>4 and 'पंचायत' in cell(headers,2) and 'एक्शनेबल' in cell(headers,4)
    fields={
        'daily':{'serial':0,'date':1,'booth':2,'panchayat':3,'name':4,'phone':5,'remarks':6},
        'registration':{'serial':0,'sector':1,'panchayat':2,'booth':3,'booth_name':4,'name':5,'father':6,'phone':7,'age':8,'occupation':9,'role':10,'date':11,'team_size':12,'status':13,'remarks':14},
        'whatsapp':{'serial':0,'sector':1,'panchayat':2,'booth':3,'group':4,'group_link':5,'additions':6,'status':7,'remarks':8},
        'actions':({'serial':0,'panchayat':2,'booth':3,'issue':4,'action':5,'type':6} if shifted else {'serial':0,'panchayat':1,'booth':2,'issue':3,'action':4,'type':5}),
        'booth':{'serial':0,'sector':1,'panchayat':2,'booth':3,'booth_name':4,'name':5,'father':6,'phone':7,'role':8,'status':9,'remarks':10},
        'social':{'serial':0,'name':1,'panchayat':2,'phone':3,'platform':4,'profile':5,'followers':6,'content':7,'remarks':8},
    }[kind]
    if date_extra is not None and kind not in ('daily','registration'):fields['date']=date_extra
    valid=[]; incompletes=0; undated=0
    # A serial alone never counts as completed work.
    substantive={'daily':['name','phone','remarks'],
                 'registration':['name','phone'],
                 'whatsapp':['group','group_link'],
                 'actions':['issue','action'],
                 'booth':['name','phone','role'],
                 'social':['name','profile']}[kind]
    for row_index,orig in enumerate(rows[idx+1:],idx+2):
        raw={k:cell(orig,col) for k,col in fields.items()}
        if not any(raw.get(f,'') for f in substantive):
            # Other populated cells cannot establish complete work.
            if any(cell(orig,k) for k in range(1,min(len(orig),12))):incompletes+=1
            continue
        date_obj=parse_date(raw.get('date',''))
        if date_obj is None:undated+=1
        raw.update({'_coordinator':worker['en'],'_key':worker['key'],'_sheet_id':worker['id'],
                    '_tab':actual_tab,'_row':row_index, '_uid':f"{worker['id']}:{kind}:{row_index}",
                    '_date':date_obj,'_incomplete_date':date_obj is None})
        if kind=='whatsapp':
            raw['additions']=to_int(raw.get('additions',''))
            raw['_group_key']=group_key(raw)
        valid.append(raw)
    return valid, {'source_rows':len(rows)-idx-1,'eligible':len(valid),'undated':undated,'incomplete':incompletes,'header_row':idx+1}


def group_key(row):
    link=str(row.get('group_link','')).strip()
    if link:
        parts=urlsplit(link if '://' in link else 'https://'+link)
        if 'chat.whatsapp.com' in parts.netloc.lower():return 'wa:'+parts.path.strip('/').lower()
        return 'url:'+parts.netloc.lower()+parts.path.rstrip('/').lower()
    name=re.sub(r'\s+',' ',str(row.get('group','')).casefold()).strip()
    return 'name:'+name if name else None


def stats(rows):
    return {'rows':len(rows),'undated':sum(r['_date'] is None for r in rows),
            'groups':len({r['_group_key'] for r in rows if r.get('_group_key')}),
            'additions':sum(to_int(r.get('additions',0)) for r in rows)}


def filter_rows(rows,worker='All Coordinators',date_from=None,date_to=None,include_undated=False,query='',booth='All booths'):
    out=[];q=str(query or '').casefold().strip()
    for r in rows:
        if worker!='All Coordinators' and r['_coordinator']!=worker:continue
        if date_from is not None or date_to is not None:
            d=r.get('_date')
            if d is None:
                if not include_undated:continue
            elif (date_from and d<date_from) or (date_to and d>date_to):continue
        if booth!='All booths' and str(r.get('booth','')).strip()!=str(booth):continue
        if q and q not in ' '.join(str(v) for k,v in r.items() if not k.startswith('_')).casefold():continue
        out.append(r)
    return out


def init_data():return {k:[] for k in TABS}


def load_online(service_account):
    import gspread
    from google.oauth2.service_account import Credentials
    creds=Credentials.from_service_account_info(dict(service_account),scopes=GOOGLE_SCOPES)
    # Parallel read: one metadata call + one values_batch_get per workbook, not 54 serial API calls.
    def read_worker(worker):
        cli=gspread.authorize(creds)
        spread=cli.open_by_key(worker['id'])
        tabmap=match_tabs([w.title for w in spread.worksheets()])
        out=init_data();health=[]
        available=[(kind,n) for kind,n in tabmap.items() if n]
        missing=[kind for kind,n in tabmap.items() if not n]
        for kind in missing:health.append({'coordinator':worker['en'],'tab':kind,'ok':False,'detail':'Tab not found','rows':0,'undated':0})
        if available:
            ranges=["'"+n.replace("'","''")+"'!A1:Q2000" for _,n in available]
            try:
                response=spread.values_batch_get(ranges,params={'valueRenderOption':'FORMATTED_VALUE'})
                payload=response.get('valueRanges',[])
                for (kind,tab),chunk in zip(available,payload):
                    try:
                        rows,info=normalize_rows(kind,chunk.get('values',[]),worker,tab)
                        out[kind].extend(rows)
                        health.append({'coordinator':worker['en'],'tab':kind,'ok':True,'detail':'Connected','rows':len(rows),'undated':info['undated'],'incomplete':info['incomplete']})
                    except Exception as exc:health.append({'coordinator':worker['en'],'tab':kind,'ok':False,'detail':f'{type(exc).__name__}: {exc}','rows':0,'undated':0})
                if len(payload)<len(available):
                    for kind,_ in available[len(payload):]:health.append({'coordinator':worker['en'],'tab':kind,'ok':False,'detail':'Missing batch response','rows':0,'undated':0})
            except Exception as exc:
                for kind,_ in available:health.append({'coordinator':worker['en'],'tab':kind,'ok':False,'detail':f'{type(exc).__name__}: {exc}','rows':0,'undated':0})
        return out,health
    data=init_data();health=[]
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs={executor.submit(read_worker,w):w for w in COORDINATORS}
        for job in as_completed(jobs):
            try:
                sub,stat=job.result()
                for kind in TABS:data[kind].extend(sub[kind])
                health.extend(stat)
            except Exception as exc:
                w=jobs[job]
                for kind in TABS:health.append({'coordinator':w['en'],'tab':kind,'ok':False,'detail':f'{type(exc).__name__}: {exc}','rows':0,'undated':0})
    for key in TABS:data[key].sort(key=lambda r:(r['_coordinator'],r['_row']))
    health.sort(key=lambda v:(v['coordinator'],v['tab']))
    return data,health


# XLSX local upload is a read-only, NON-LIVE snapshot mode. No external dependencies.
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def _colnum(addr):
    n=0
    for char in re.match(r'[A-Z]+',addr).group():n=n*26+ord(char)-64
    return n-1

def parse_xlsx(buf):
    z=zipfile.ZipFile(io.BytesIO(buf))
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        ss=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(elem.itertext()) for elem in ss.findall('m:si',NS)]
    root=ET.fromstring(z.read('xl/workbook.xml'))
    rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    mapping={e.get('Id'):e.get('Target') for e in rel}
    result={}
    for sh in root.findall('m:sheets/m:sheet',NS):
        name=sh.get('name');target=mapping[sh.get('{'+NS['r']+'}id')]
        p=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        if p not in z.namelist():p='xl/'+p.replace('xl/','')
        if p not in z.namelist():continue
        xml=ET.fromstring(z.read(p))
        rows=[]
        for row in xml.findall('m:sheetData/m:row',NS):
            vals={}
            for c in row.findall('m:c',NS):
                ref=c.get('r'); value=c.find('m:v',NS);inline=c.find('m:is',NS)
                txt=value.text if value is not None else (''.join(inline.itertext()) if inline is not None else '')
                if txt is None:continue
                if c.get('t')=='s':txt=strings[int(txt)]
                elif c.get('t')=='inlineStr':txt=''.join(inline.itertext()) if inline is not None else ''
                if str(txt).strip():vals[_colnum(ref)]=str(txt)
            if vals:
                width=min(20,max(vals)+1)
                rows.append([vals.get(i,'') for i in range(width)])
        result[name]=rows
    return result


def load_snapshots(files):
    data=init_data();health=[];done=set()
    for f in files:
        name=getattr(f,'name','')
        w=next((w for w in COORDINATORS if name.lower().startswith(w['key'].lower()+' ')),None)
        if not w:continue
        done.add(w['key'])
        try:
            tabs=parse_xlsx(f.getvalue() if hasattr(f,'getvalue') else f.read())
            mapping=match_tabs(list(tabs))
            for kind,actual in mapping.items():
                if not actual:
                    health.append({'coordinator':w['en'],'tab':kind,'ok':False,'detail':'Tab absent from upload','rows':0,'undated':0});continue
                records,info=normalize_rows(kind,tabs[actual],w,actual)
                data[kind].extend(records)
                health.append({'coordinator':w['en'],'tab':kind,'ok':True,'detail':'Uploaded snapshot — not live','rows':len(records),'undated':info['undated']})
        except Exception as exc:
            for kind in TABS:health.append({'coordinator':w['en'],'tab':kind,'ok':False,'detail':str(exc),'rows':0,'undated':0})
    for w in COORDINATORS:
        if w['key'] not in done:
            for kind in TABS:health.append({'coordinator':w['en'],'tab':kind,'ok':False,'detail':'Workbook not uploaded','rows':0,'undated':0})
    return data,health


SAMPLE={
'daily': [('Vivek','2026-10-14','101','समदा'),('Sujeet','2026-10-14','346','बरुआ'),('Nikhil','2026-10-15','111','पंडरिया')],
'whatsapp':[('Vivek','2026-10-14','MG-A',10),('Sujeet','2026-10-14','MG-A',15),('Sateesh','2026-10-15','MG-B',12)],
}
def load_sample():
    data=init_data()
    for i,(who,d,booth,village) in enumerate(SAMPLE['daily']):
        w=next(w for w in COORDINATORS if w['key']==who)
        data['daily'].append({'_uid':str(i),'_coordinator':w['en'],'_key':who,'_row':i+2,'_date':parse_date(d),'date':d,'booth':booth,'panchayat':village,'name':'Sample person','remarks':'Demo only'})
    for i,(who,d,group,add) in enumerate(SAMPLE['whatsapp']):
        w=next(w for w in COORDINATORS if w['key']==who)
        data['whatsapp'].append({'_uid':'w'+str(i),'_coordinator':w['en'],'_key':who,'_row':i+2,'_date':parse_date(d),'date':d,'group':group,'_group_key':'group:'+group,'additions':add})
    return data,[{'coordinator':w['en'],'tab':kind,'ok':True,'detail':'Fictional sample','rows':0,'undated':0} for w in COORDINATORS for kind in TABS]

CATEGORY_TRANSLATION={'सक्रिय':'Active','निष्क्रिय':'Inactive','लंबित':'Pending','बना':'Created','नया':'New','सामान्य':'General','पोचिंग':'Outreach','एक्शनेबल':'Actionable','स्टूडेंट':'Student','प्रगति में':'In progress','पूर्ण':'Completed','बूथ प्रभारी':'Booth in-charge','सेक्टर प्रभारी':'Sector in-charge'}
REVERSE_TRANSLATION={v.lower():k for k,v in CATEGORY_TRANSLATION.items()}
def display_value(key,value,lang):
    value=str(value or '').strip()
    if lang=='English' and key in ('status','type','occupation','role'):
        return CATEGORY_TRANSLATION.get(value,value)
    if lang=='हिंदी' and key in ('status','type','occupation','role'):
        return REVERSE_TRANSLATION.get(value.lower(),value)
    return value

def mask_phone(value):
    value=str(value or '').strip()
    digits=re.sub(r'\D','',value)
    if len(digits)>=8:return '••••••'+digits[-4:]
    return '—' if not digits else '••••'

def normalized_booth(raw):
    """Do NOT reinterpret scientific notation or concatenated booth numbers as a single booth."""
    s=str(raw or '').strip()
    if re.fullmatch(r'\d+\.0+',s):return s.split('.')[0]
    if re.search(r'[Ee]\+?',s):return s+' ⚠'
    return s
