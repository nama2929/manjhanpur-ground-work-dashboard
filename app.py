"""Saarthi Analytics | Manjhanpur 252 Constituency Operations V5.
Read-only reporting from the same nine original Google Sheets as V4.
No credentials or private data are bundled in this repository.
"""
from __future__ import annotations

import base64
import csv
import datetime as dt
import hmac
import html
import io
from pathlib import Path
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import COORDINATORS, TABS, SECTION_FIELDS, FIELD_NAMES
from data_layer import (
    init_data, load_online, load_snapshots, load_sample, filter_rows,
    stats, mask_phone, normalized_booth, to_int, display_value,
)
from view_logic import trend, coordinator_activity, category_counts, group_summary, summarize_section, daily_matrix

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "saarthi-logo.png"
FAVICON = ROOT / "assets" / "saarthi-favicon.png"
LOGO_URI = 'data:image/png;base64,' + base64.b64encode(LOGO.read_bytes()).decode('ascii')
st.set_page_config(
    page_title="Saarthi Analytics | Manjhanpur 252",
    page_icon=str(FAVICON), layout="wide", initial_sidebar_state="collapsed",
)
try:
    st.logo(str(LOGO), icon_image=str(FAVICON), size="large")
except (AttributeError, TypeError):
    pass

NOW = dt.datetime.now(ZoneInfo("Asia/Kolkata"))
ALL = "All Coordinators"
PAGES = ["home", "reports", "dates", "team"]
PORTRAIT_MP = 'https://assets.telegraphindia.com/telegraph/2024/Jun/1718003396_pushpendra-saroj_facebook_pushpendra-saroj-1.jpg'
PORTRAIT_MLA = 'https://www.jansatta.com/wp-content/uploads/2025/04/indrajeet-saroj.jpg'
PALETTE = {"orange": "#bf642d", "deep": "#29394b", "sage": "#43867b", "blue": "#587fac"}

LABEL = {
    'English': {
        'home':'Home','reports':'Reports','dates':'Daily Summary','team':'Team','health':'Connection Status',
        'worker':'Coordinator','period':'Period','all':'All dates','today':'Today','yesterday':'Yesterday',
        'week':'Last 7 days','month':'Last 30 days','custom':'Custom dates','any':'All coordinators',
        'undated':'Also include undated entries','booth':'Booth','village':'Panchayat / Village',
        'search':'Search records','filter':'Filters','section':'Choose report','charts':'Charts',
        'table':'Detailed records','download':'Download CSV','title':'Ground Operations Dashboard',
        'subtitle':'Manjhanpur Assembly 252 • Office of MP Pushpendra Saroj',
        'recent':'Recent dated reports','byworker':'Coordinator-wise work','bydate':'Daily reporting trend',
        'wa':'Reported WhatsApp additions','groups':'Unique WhatsApp groups',
        'registrations':'Worker registrations','booths':'Booths visited','observations':'Actionable records',
        'entries':'Total report entries','nodata':'No records match the current filters.',
        'nodates':'No dated records are available for this selection.', 'unknown':'Entries without dates',
        'team_title':'Coordinator Overview', 'quick':'Open a report', 'office':'Office view',
        'refresh':'Refresh data','login':'Office sign in','data':'Source', 'source':'Connection',
        'metrics':'At a glance','records':'Records','status':'Current reporting status',
    },
    'हिंदी': {
        'home':'होम','reports':'रिपोर्ट','dates':'दिनांकवार सार','team':'टीम','health':'कनेक्शन स्थिति',
        'worker':'संयोजक','period':'अवधि','all':'सभी तारीखें','today':'आज','yesterday':'कल',
        'week':'पिछले 7 दिन','month':'पिछले 30 दिन','custom':'तारीख चुनें','any':'सभी संयोजक',
        'undated':'बिना तारीख वाली एंट्री भी शामिल करें','booth':'बूथ','village':'पंचायत / गांव',
        'search':'रिकॉर्ड खोजें','filter':'फिल्टर','section':'रिपोर्ट चुनें','charts':'ग्राफ',
        'table':'विस्तृत रिकॉर्ड','download':'CSV डाउनलोड','title':'फील्ड ऑपरेशंस डैशबोर्ड',
        'subtitle':'मंझनपुर विधानसभा 252 • सांसद पुष्पेन्द्र सरोज कार्यालय',
        'recent':'हाल की दिनांकित रिपोर्ट','byworker':'संयोजक अनुसार काम','bydate':'दिनांकवार काम का ग्राफ',
        'wa':'व्हॉट्सऐप पर रिपोर्ट किए नए सदस्य','groups':'अलग व्हॉट्सऐप ग्रुप',
        'registrations':'कार्यकर्ता पंजीकरण','booths':'दौरे वाले बूथ','observations':'कार्रवाई योग्य रिकॉर्ड',
        'entries':'कुल रिपोर्ट एंट्री','nodata':'चुने हुए फिल्टर में रिकॉर्ड नहीं मिले।',
        'nodates':'चुनी हुई अवधि में दिनांकित रिकॉर्ड नहीं हैं।','unknown':'बिना तारीख के रिकॉर्ड',
        'team_title':'संयोजक सारांश','quick':'रिपोर्ट खोलें','office':'कार्यालय दृश्य',
        'refresh':'डेटा रीफ़्रेश','login':'कार्यालय लॉगिन','data':'डेटा स्रोत','source':'कनेक्शन',
        'metrics':'एक नज़र में','records':'रिकॉर्ड','status':'मौजूदा रिपोर्टिंग स्थिति',
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--sa-orange:#bf642d;--sa-dark:#29394b;--sa-cream:#fff8f2;--sa-edge:#e7e2db;--sa-text:#263846}
html,body,[data-testid="stAppViewContainer"]{font-family:'Manrope','Hind',sans-serif!important;color:var(--sa-text)}
.stApp{background:#fbf9f6;color:var(--sa-text)}
.block-container{max-width:1310px;padding:1.05rem 2.1rem 3.2rem}
h1,h2,h3{font-family:'Manrope','Hind',sans-serif!important;color:#273847;letter-spacing:-.025em!important}
[data-testid="stSidebar"]{background:#fffaf5;border-right:1px solid #e9e2d9}
[data-testid="stSidebar"] *{color:#29394b!important}
[data-testid="stSidebar"] button{color:#263846!important;background:#f5eae0!important;border:1px solid #e3cbb8!important}
[data-testid="stSidebar"] a{color:#b85f2c!important}
button[kind="primary"], [data-testid="stBaseButton-primary"] {background:#bb5c2c!important;color:white!important;border:1px solid #bb5c2c!important}
button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{background:#9e4924!important;color:#fff!important}
.stButton>button,div[data-testid="stDownloadButton"]>button{background:#fff!important;color:#813c21!important;border:1px solid #dfbaa0!important;border-radius:12px!important;font-weight:750!important;min-height:46px!important;box-shadow:0 2px 6px rgba(111,60,33,.04)!important}
.stButton>button:hover,div[data-testid="stDownloadButton"]>button:hover{background:#fff0e5!important;color:#71361e!important;border-color:#b86a3f!important}
[data-testid="stTabs"] [role="tablist"]{gap:.5rem;overflow-x:auto;white-space:nowrap}
[data-testid="stTabs"] [role="tab"]{color:#6d625b!important;font-weight:750!important;min-height:46px}
[data-testid="stTabs"] [aria-selected="true"]{color:#af542b!important;border-bottom-color:#bf642d!important}
[data-testid="stSegmentedControl"] button{border-radius:11px!important;min-height:42px!important;font-weight:700!important;color:#513c30!important}
[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#bd632d!important;color:white!important}
div[data-baseweb="select"]>div{background:#fff!important;color:#283b4d!important;border-color:#ded6ce!important;min-height:47px!important}
[data-baseweb="select"] input,input,textarea{background:#fff!important;color:#263846!important}
[data-testid="stDataFrame"]{border:1px solid #e3e2dd!important;border-radius:13px!important;overflow:hidden}
[data-testid="stExpander"]{background:#fff!important;border:1px solid #e9e1d7!important;border-radius:12px!important}
[data-testid="stAlert"]{border-radius:13px}
[data-testid="stSelectbox"] label,[data-testid="stDateInput"] label,[data-testid="stTextInput"] label{color:#485d6c!important;font-weight:650!important}
.brand-shell{background:white;border:1px solid #eadfd4;border-top:4px solid #c46b30;border-radius:20px;padding:13px 19px;display:flex;gap:16px;align-items:center;justify-content:space-between;margin-bottom:11px;box-shadow:0 8px 26px rgba(50,41,29,.035)}
.brand-left{display:flex;align-items:center;gap:15px;min-width:0}
.brand-logo{height:74px;width:74px;object-fit:contain;border-radius:50%;flex-shrink:0;background:#fff}
.brand-title{font-size:1.26rem;letter-spacing:-.04em;font-weight:850;color:#273847;line-height:1.12}
.brand-tag{font-size:.72rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:#ba602e;padding-top:5px}
.brand-right{text-align:right;white-space:nowrap;color:#637383;font-size:.78rem}
.brand-right strong{color:#af592d;display:block;font-weight:800;font-size:.85rem}
.hero{background:linear-gradient(120deg,#fffefd 0%,#fff8f2 62%,#f6e8da 100%);border:1px solid #e6dbce;border-radius:20px;padding:25px 29px;margin:13px 0 17px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:240px;height:240px;border:1px solid rgba(190,107,54,.18);border-radius:50%;right:-70px;top:-120px}
.hero-eyebrow{color:#ba602e;font-size:.73rem;letter-spacing:.15em;font-weight:800;text-transform:uppercase;position:relative}
.hero h1{font-size:clamp(1.55rem,3vw,2.65rem);line-height:1.16;margin:9px 0 8px;color:#273847!important;position:relative;font-weight:850}
.hero p{font-size:.95rem;color:#526979;margin:0;position:relative}
.section-head{font-size:1.17rem;font-weight:850;color:#25394b;margin:22px 0 12px;letter-spacing:-.018em}
.section-kicker{font-weight:750;font-size:.7rem;letter-spacing:.15em;color:#ad5c30;text-transform:uppercase;margin:15px 0 4px}
.subtle{color:#677988;font-size:.84rem}
.fine-note{padding:11px 14px;background:#fff8e9;border:1px solid #eedeb8;color:#775a2a;border-radius:12px;font-size:.83rem;line-height:1.6;margin:8px 0 13px}
.people-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:0 0 15px}
.person{background:#fff;border:1px solid #e8e1d9;border-radius:17px;display:flex;gap:14px;padding:12px;align-items:center;min-width:0}
.person img{width:112px;height:120px;flex-shrink:0;object-fit:cover;object-position:50% 22%;border-radius:10px;background:#eae3dc}
.person strong{display:block;color:#25394a;font-weight:850;font-size:1rem;line-height:1.3}
.person small{display:block;color:#ac6039;font-size:.72rem;font-weight:750;padding-top:5px}
.person span{display:block;color:#657787;font-size:.76rem;padding-top:6px;line-height:1.35}
.kpi-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px;margin:5px 0 17px}
.kpi{background:#fff;border:1px solid #e7e0d7;border-radius:17px;padding:17px 16px;min-height:112px;position:relative;box-shadow:0 5px 16px rgba(50,41,29,.02)}
.kpi:before{content:"";position:absolute;top:16px;right:14px;height:8px;width:8px;border-radius:100%;background:#ce8051}
.kpi-label{font-size:.77rem;color:#657687;font-weight:750;line-height:1.45;max-width:92%}
.kpi-value{font-size:clamp(1.5rem,3vw,2.25rem);font-weight:850;letter-spacing:-.045em;color:#243648;margin:8px 0 0}
.kpi-context{font-size:.69rem;color:#a36f50;margin-top:5px}
.source-state{display:flex;gap:9px;align-items:center;font-size:.83rem;color:#506473;margin:4px 0 12px;flex-wrap:wrap}
.state-chip{background:#eaf6ef;color:#226e51;border:1px solid #b9ddc6;border-radius:99px;padding:5px 11px;font-weight:750}
.state-chip.warn{background:#fff3e6;color:#a15b29;border-color:#eacaaa}
.footer-sa{display:flex;align-items:center;gap:11px;border-top:1px solid #e6ddd5;padding:16px 0;margin-top:29px;color:#6d7780;font-size:.74rem}
.footer-sa img{height:44px;width:44px;object-fit:contain;flex-shrink:0}
.footer-sa b{color:#a65b33}
.report-heading{font-weight:850;font-size:1.1rem;color:#283b4d;margin:9px 0}
.download-row{margin:10px 0}
@media(max-width:980px){.block-container{padding:1.0rem 1.3rem 3rem}.brand-logo{width:63px;height:63px}.kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.person img{width:92px;height:105px}}
@media(max-width:700px){
 .block-container{padding:.6rem .75rem 4rem!important;max-width:100%!important}
 .brand-shell{padding:10px 12px;gap:8px;border-radius:13px}
 .brand-left{gap:8px}.brand-logo{width:49px;height:49px}
 .brand-title{font-size:.99rem}.brand-tag{font-size:.55rem;letter-spacing:.07em}
 .brand-right{font-size:.59rem}.brand-right strong{font-size:.65rem}
 .hero{padding:17px 16px;margin:8px 0 13px;border-radius:15px}.hero h1{font-size:1.65rem}
 .hero p{font-size:.83rem}.hero-eyebrow{font-size:.61rem}
 .people-grid{gap:8px}.person{flex-direction:column;text-align:center;padding:8px 5px;gap:7px;min-height:0}
 .person img{width:90px;height:106px;max-width:100%}.person strong{font-size:.76rem}.person small{font-size:.63rem}.person span{font-size:.65rem}
 .kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.kpi{padding:13px 11px;min-height:96px}
 .kpi-label{font-size:.69rem}.kpi-value{font-size:1.65rem}.section-head{font-size:1.03rem;margin:16px 0 8px}
 .footer-sa{font-size:.65rem}.footer-sa img{width:36px;height:36px}
 [data-testid="stTabs"] [role="tablist"]{overflow-x:auto!important}
 .stButton>button{min-height:49px!important;font-size:.88rem!important}
 div[data-testid="stHorizontalBlock"]{gap:.5rem}
}
@media(max-width:360px){.brand-right{display:none}.kpi-grid{grid-template-columns:1fr 1fr}.kpi-value{font-size:1.48rem}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def esc(v):return html.escape(str(v), quote=True)

def tr(key):return LABEL[lang][key]

def brand_header():
    status = ("Office brief" if lang == 'English' else 'कार्यालय रिपोर्ट')
    st.markdown(f'''<div class="brand-shell">
       <div class="brand-left"><img class="brand-logo" src="{LOGO_URI}" alt="Saarthi Analytics"/>
         <div><div class="brand-title">SAARTHI ANALYTICS</div><div class="brand-tag">Constituency Intelligence • Manjhanpur 252</div></div></div>
       <div class="brand-right"><strong>{esc(status)}</strong>{NOW.strftime('%d %b %Y')} · IST</div>
    </div>''',unsafe_allow_html=True)

def hero(title, subtitle='', eyebrow='MANJHANPUR • ASSEMBLY 252'):
    st.markdown(f'<div class="hero"><div class="hero-eyebrow">{esc(eyebrow)}</div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)

def heading(title):
    st.markdown(f'<div class="section-head">{esc(title)}</div>', unsafe_allow_html=True)

def metric_cards(pairs, context=''):
    cards=''.join(f'<div class="kpi"><div class="kpi-label">{esc(k)}</div><div class="kpi-value">{esc(f"{v:,}" if isinstance(v,int) else v)}</div><div class="kpi-context">{esc(context)}</div></div>' for k,v in pairs)
    st.markdown(f'<div class="kpi-grid">{cards}</div>',unsafe_allow_html=True)

def make_chart(items,label_col,value_col,horizontal=False,mode='bar',height=260,color=None):
    if not items:return False
    df=pd.DataFrame(items)
    if df.empty or sum(to_int(v) for v in df[value_col])==0:return False
    color=color or PALETTE['orange']
    base=alt.Chart(df).encode(tooltip=[alt.Tooltip(label_col,type='nominal'),alt.Tooltip(value_col,type='quantitative')])
    if horizontal:
        ch=base.mark_bar(color=color,cornerRadiusEnd=5).encode(y=alt.Y(f'{label_col}:N',sort='-x',title=None,axis=alt.Axis(labelLimit=180)),x=alt.X(f'{value_col}:Q',title=None))
    elif mode=='line':
        ch=base.mark_line(point=alt.OverlayMarkDef(filled=True,size=65),color=color,strokeWidth=3).encode(x=alt.X(f'{label_col}:N',title=None,axis=alt.Axis(labelAngle=-30)),y=alt.Y(f'{value_col}:Q',title=None,scale=alt.Scale(zero=True)))
    else:
        ch=base.mark_bar(color=color,cornerRadiusEnd=5).encode(x=alt.X(f'{label_col}:N',title=None,axis=alt.Axis(labelAngle=-30)),y=alt.Y(f'{value_col}:Q',title=None))
    st.altair_chart(ch.properties(height=height).configure_view(strokeWidth=0).configure_axis(labelColor='#607080',titleColor='#607080',gridColor='#ede6df'),use_container_width=True)
    return True

def csv_file(records):
    if not records:return b''
    f=io.StringIO();out=csv.DictWriter(f,fieldnames=list(records[0]))
    out.writeheader()
    for rec in records:
        out.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in rec.items()})
    return f.getvalue().encode('utf-8-sig')

def person_name(name):
    if name==ALL:return tr('any')
    return next((p['hi'] for p in COORDINATORS if p['en']==name),name) if lang=='हिंदी' else name

def public_rows(rows,kind):
    result=[]
    for r in rows:
        row={tr('worker'):person_name(r.get('_coordinator',''))}
        for field in SECTION_FIELDS[kind]:
            val=r.get(field,'')
            if field=='date':val=r['_date'].isoformat() if r.get('_date') else ('Undated' if lang=='English' else 'बिना तारीख')
            elif field=='phone':val=mask_phone(val)
            elif field=='group_link':val='—'
            elif field=='booth':val=normalized_booth(val)
            elif field in ('additions','team_size','followers'):val=to_int(val)
            else:val=display_value(field,val,lang)
            row[FIELD_NAMES[field][0 if lang=='English' else 1]]=val
        result.append(row)
    return result

def table_export(rows,kind,key):
    st.caption(f'{len(rows):,} '+('matching records' if lang=='English' else 'रिकॉर्ड'))
    if not rows:st.info(tr('nodata'));return
    presented=public_rows(rows,kind)
    st.dataframe(presented,hide_index=True,use_container_width=True,height=min(520,95+36*len(rows)))
    st.download_button('⬇ '+tr('download'),csv_file(presented),file_name=f'saarthi_manjhanpur_{kind}_{NOW.date()}.csv',mime='text/csv',key=key)

def set_page(page): st.session_state['page_v5']=page

def date_choice(key):
    opts=['all','today','yesterday','week','month','custom']
    period=st.selectbox(tr('period'),opts,format_func=tr,key=f'{key}_period')
    today=NOW.date();low=high=None
    if period=='today':low=high=today
    elif period=='yesterday':low=high=today-dt.timedelta(days=1)
    elif period=='week':low=today-dt.timedelta(days=6);high=today
    elif period=='month':low=today-dt.timedelta(days=29);high=today
    elif period=='custom':
        dates=st.date_input('From / To · से / तक',value=(today-dt.timedelta(days=7),today),key=f'{key}_range')
        if isinstance(dates,(list,tuple)) and len(dates)==2:low,high=dates
        else:st.info('Select a start and end date / शुरू और अंतिम तारीख चुनें')
    include=False
    if period!='all':include=st.checkbox(tr('undated'),key=f'{key}_undated',value=False)
    return low,high,include

def filters(key,kind=None):
    c1,c2=st.columns(2,gap='small')
    with c1:person=st.selectbox(tr('worker'),[ALL]+[p['en'] for p in COORDINATORS],format_func=person_name,key=f'{key}_person')
    with c2:low,high,include=date_choice(key)
    booth='All booths';query=''
    if kind:
        with st.expander('🔎 '+tr('filter'),expanded=False):
            options=sorted({normalized_booth(r.get('booth')) for r in data[kind] if normalized_booth(r.get('booth'))})
            booth=st.selectbox(tr('booth'),['All booths']+options,key=f'{key}_booth')
            q=st.text_input(tr('search'),key=f'{key}_search',placeholder='Name, village, issue… / नाम, गांव, समस्या…')
            query=q
    return person,low,high,include,booth,query

def wa_note(records):
    if any(r.get('_date') is None for r in records):
        st.markdown('<div class="fine-note">'+esc('⚠ Some WhatsApp entries have no recorded date; they count in all-time totals, never in a dated chart.' if lang=='English' else '⚠ कुछ व्हॉट्सऐप एंट्री की तारीख नहीं है। वे कुल आँकड़े में हैं, दिनांकवार ग्राफ में नहीं।')+'</div>',unsafe_allow_html=True)

def footer():
    st.markdown(f'''<div class="footer-sa"><img src="{LOGO_URI}" alt="Saarthi Analytics logo"/>
      <div><b>Saarthi Analytics</b> · Constituency Intelligence<br/>
       {esc('Office of MP Pushpendra Saroj · Read-only reporting · Last checked' if lang=='English' else 'सांसद पुष्पेन्द्र सरोज कार्यालय · केवल रिपोर्टिंग · अंतिम जांच')}:
       {NOW.strftime('%d %b %Y %I:%M %p IST')}</div></div>''',unsafe_allow_html=True)

# Authentication. Office data is never rendered to unauthenticated visitors.
try: SECRETS=dict(st.secrets)
except Exception: SECRETS={}
account=SECRETS.get('gcp_service_account')
password=str(SECRETS.get('dashboard_password','')).strip()
if 'page_v5' not in st.session_state:st.session_state.page_v5='home'
if 'report_v5' not in st.session_state:st.session_state.report_v5='daily'
if 'language_v5' not in st.session_state:st.session_state.language_v5='English'
lang=st.session_state.language_v5
if account and password and not st.session_state.get('office_auth_v5',False):
    brand_header();hero(tr('login'),'Authorized office access only / केवल अधिकृत कार्यालय उपयोग')
    with st.form('office_login_v5'):
        entered=st.text_input('Office password / कार्यालय पासवर्ड',type='password')
        if st.form_submit_button('Sign in / प्रवेश',type='primary',use_container_width=True):
            if hmac.compare_digest(entered,password):
                st.session_state.office_auth_v5=True;st.rerun()
            else:st.error('Incorrect password / गलत पासवर्ड')
    st.stop()

# Technical settings deliberately kept out of the MP's primary navigation.
with st.sidebar:
    st.image(str(LOGO),width=115)
    st.markdown('### Saarthi Analytics')
    st.caption('Manjhanpur 252 · Office tools / कार्यालय सेटिंग')
    source=st.selectbox('Data source / डेटा स्रोत', ['Live Google Sheets','Sample (fictional)','Upload XLSX (offline)'],key='source_v5')
    if st.button('🔄 '+tr('refresh'),use_container_width=True,key='reload_side_v5'):
        st.cache_data.clear();st.rerun()
    with st.expander('🔒 Data connection / कनेक्शन'):
        if st.button('View connection status',key='goto_health_v5',use_container_width=True,on_click=set_page,args=('health',)):
            pass
        st.caption('9 original sheets · 54 report tabs')
        for person in COORDINATORS:
            st.markdown(f'[{person["en"]}](https://docs.google.com/spreadsheets/d/{person["id"]}/edit)')
    if account and password and st.session_state.get('office_auth_v5',False):
        if st.button('Sign out',key='signout_v5'):
            st.session_state.office_auth_v5=False;st.rerun()

if source=='Live Google Sheets' and account and not password:
    st.error('Set dashboard_password in Streamlit Secrets. Do not display private data without authentication.')
    st.stop()

health=[];data=init_data();loaded=False;failure=None
if source=='Live Google Sheets':
    if account and password:
        st_autorefresh(interval=60_000,key='refresh_timer_v5')
        @st.cache_data(ttl=48,show_spinner='Reading the nine original Google Sheets…')
        def online(_account):return load_online(_account)
        try:
            data,health=online(account)
            loaded=any(t.get('ok') for t in health)
        except Exception as exc:
            failure=f'{type(exc).__name__}: {exc}'
    else:failure='Live Google service account configuration is missing.'
elif source=='Sample (fictional)':
    data,health=load_sample();loaded=True
else:
    files=st.sidebar.file_uploader('Upload 9 worksheets',type=['xlsx'],accept_multiple_files=True)
    if files:
        data,health=load_snapshots(files)
        loaded=any(t.get('ok') for t in health)

connected=sum(1 for entry in health if entry.get('ok'))
total=len(COORDINATORS)*len(TABS)

brand_header()
# Four obvious MP navigation options, same logic on mobile and large screens.
nav1,nav2=st.columns([3.8,1],gap='small')
with nav2:
    lang=st.selectbox('Language / भाषा',['English','हिंदी'],key='language_v5')
with nav1:
    page=st.segmented_control('Navigate / चुनें',PAGES + (['health'] if st.session_state.page_v5=='health' else []),
                              selection_mode='single',format_func=lambda p:('⚙ '+tr('health') if p=='health' else {
                               'home':'⌂ '+tr('home'),'reports':'▣ '+tr('reports'),
                               'dates':'▤ '+tr('dates'),'team':'♙ '+tr('team')}[p]),
                              key='page_v5',label_visibility='visible')
if page is None:
    page='home'
if source=='Live Google Sheets':
    if loaded and connected==total:
        state=f'{connected}/{total} '+('tabs connected' if lang=='English' else 'टैब जुड़े हुए')
        classname='state-chip'
    elif loaded:
        state=f'{connected}/{total} '+('partial connection' if lang=='English' else 'आंशिक कनेक्शन')
        classname='state-chip warn'
    else:
        state=('Connection unavailable' if lang=='English' else 'कनेक्शन उपलब्ध नहीं')
        classname='state-chip warn'
    st.markdown(f'<div class="source-state"><span class="{classname}">{esc(state)}</span><span>{esc("Read-only • last checked" if lang=="English" else "केवल पढ़ने हेतु • अंतिम जांच")} {NOW.strftime("%I:%M %p IST")}</span></div>',unsafe_allow_html=True)
else:
    st.warning('Offline / fictional preview. Not connected to live sheets.' if lang=='English' else 'डेमो डेटा। लाइव शीट से जुड़ा हुआ नहीं।')

if page=='home':
    hero(tr('title'),tr('subtitle'))
    st.markdown(f'''<div class="people-grid">
       <div class="person"><img src="{PORTRAIT_MP}" alt="MP Pushpendra Saroj"/>
         <div><small>MEMBER OF PARLIAMENT</small><strong>MP Pushpendra Saroj</strong><span>Kaushambi · Lok Sabha</span></div></div>
       <div class="person"><img src="{PORTRAIT_MLA}" alt="MLA Indrajeet Saroj"/>
         <div><small>MEMBER OF LEGISLATIVE ASSEMBLY</small><strong>MLA Indrajeet Saroj</strong><span>Manjhanpur · Assembly 252</span></div></div>
       </div>''',unsafe_allow_html=True)
    heading(tr('metrics'))
    who,low,high,include,*_=filters('home')
    if loaded:
        picked={kind:filter_rows(data[kind],who,low,high,include) for kind in TABS}
        summary={kind:summarize_section(picked[kind],kind) for kind in TABS}
        metric_cards([(tr('wa'),summary['whatsapp']['additions']),
                      (tr('groups'),summary['whatsapp']['groups']),
                      (tr('registrations'),summary['registration']['records']),
                      (tr('booths'),summary['daily']['booths']),
                      (tr('observations'),summary['actions']['records']),
                      (tr('entries'),sum(summary[k]['records'] for k in TABS))],
                     'As reported / दर्ज रिपोर्ट')
        wa_note(picked['whatsapp'])
        left,right=st.columns([1,1],gap='medium')
        everyone=[r for kind in TABS for r in picked[kind]]
        with left:
            heading(tr('byworker'))
            work=coordinator_activity(everyone,'daily',lang,include_zeros=True)
            if not make_chart(work,'Coordinator','Value',horizontal=True,height=305):st.info(tr('nodata'))
            st.caption('Chart counts report rows, not unique people.' if lang=='English' else 'ग्राफ एंट्री गिनता है, अलग व्यक्तियों को नहीं।')
        with right:
            heading(tr('bydate'))
            daily={}
            for r in everyone:
                if r.get('_date'):
                    date=r['_date'].isoformat();daily[date]=daily.get(date,0)+1
            if not make_chart([{'Date':d,'Value':v} for d,v in sorted(daily.items())],'Date','Value',mode='line',height=305):
                st.info(tr('nodates'))
        heading(tr('quick'))
        c1,c2,c3=st.columns(3,gap='small')
        with c1:st.button('▣ '+tr('reports'),on_click=set_page,args=('reports',),use_container_width=True,type='primary',key='go_reports_v5')
        with c2:st.button('▤ '+tr('dates'),on_click=set_page,args=('dates',),use_container_width=True,key='go_dates_v5')
        with c3:st.button('♙ '+tr('team'),on_click=set_page,args=('team',),use_container_width=True,key='go_team_v5')
    else:
        st.warning('Connection is not ready. Open Connection Status from Office tools. No figures are fabricated.' if lang=='English' else 'कनेक्शन चालू नहीं है। कार्यालय सेटिंग से कनेक्शन जांचें।')
        if failure:st.caption(failure)

elif page=='reports':
    hero(tr('reports'),'Select one report, apply filters, then view charts and records.' if lang=='English' else 'रिपोर्ट चुनें, फिल्टर लगाएँ और ग्राफ तथा रिकॉर्ड देखें।')
    kind=st.selectbox(tr('section'),list(TABS),format_func=lambda k:TABS[k]['hi' if lang=='हिंदी' else 'en'],key='report_v5')
    who,low,high,include,booth,query=filters('reports_'+kind,kind)
    if loaded:
        records=filter_rows(data[kind],who,low,high,include,query=query,booth=booth)
        summary=summarize_section(records,kind)
        pairs=[(tr('entries'),summary['records']),(tr('unknown'),summary['undated'])]
        if kind=='whatsapp':pairs += [(tr('wa'),summary['additions']),(tr('groups'),summary['groups'])]
        else:pairs += [(tr('booths'),summary['booths']),(tr('worker'),summary['coordinators'])]
        metric_cards(pairs)
        if kind=='whatsapp':
            wa_note(records)
            st.caption('Group count deduplicated by link/ID when available; additions are reported events, not proven unique individuals.' if lang=='English' else 'ग्रुप लिंक/नाम अनुसार अलग गिने जाते हैं। नए सदस्य की एंट्री अलग व्यक्ति होने का प्रमाण नहीं है।')
        graph_tab,rows_tab=st.tabs(['📊 '+tr('charts'),'📋 '+tr('table')])
        with graph_tab:
            c1,c2=st.columns(2,gap='medium')
            with c1:
                heading(tr('byworker'))
                if not make_chart(coordinator_activity(records,kind,lang),'Coordinator','Value',horizontal=True,height=285):st.info(tr('nodata'))
            with c2:
                heading(tr('bydate'))
                if not make_chart(trend(records,kind),'Date','Value',mode='line',height=285):st.info(tr('nodates'))
            category_field={'registration':'status','actions':'type','booth':'status','social':'platform','daily':'panchayat','whatsapp':'status'}.get(kind)
            categories=category_counts(records,category_field,lang) if category_field else []
            if categories:
                heading(FIELD_NAMES.get(category_field,('Category','श्रेणी'))[0 if lang=='English' else 1])
                make_chart(categories,'Category','Value',horizontal=True,height=min(340,max(150,35*len(categories))),color=PALETTE['sage'])
            if kind=='whatsapp':
                heading('WhatsApp group summary / ग्रुप सारांश')
                st.dataframe(group_summary(records,lang),hide_index=True,use_container_width=True)
        with rows_tab:table_export(records,kind,'export_'+kind)
    else:st.info('No live source connected yet.' if lang=='English' else 'लाइव स्रोत अभी जुड़ा नहीं है।')

elif page=='dates':
    hero(tr('dates'),'Date-by-date reporting; WhatsApp additions are a separate measure.' if lang=='English' else 'दिनांकवार रिपोर्ट। व्हॉट्सऐप नए सदस्य अलग आँकड़ा है।')
    who,low,high,include,*_=filters('date_report')
    if loaded:
        matrix=daily_matrix(data,who,low,high,include,filter_rows)
        scoped={k:filter_rows(data[k],who,low,high,include) for k in TABS}
        metric_cards([(TABS[k]['hi' if lang=='हिंदी' else 'en'],stats(v)['additions'] if k=='whatsapp' else len(v)) for k,v in scoped.items()])
        byday=[{'Date':r['Date'],'Value':sum(r[k] for k in TABS if k!='whatsapp')} for r in matrix]
        wa=[{'Date':r['Date'],'Value':r['whatsapp']} for r in matrix]
        c1,c2=st.columns(2,gap='medium')
        with c1:
            heading('Report entries / रिपोर्ट एंट्री')
            if not make_chart(byday,'Date','Value',mode='line'):st.info(tr('nodates'))
        with c2:
            heading(tr('wa'))
            if not make_chart(wa,'Date','Value'):st.info(tr('nodates'))
        heading(tr('table'))
        if matrix:
            table=[{'Date / दिनांक':r['Date'],**{TABS[k]['hi' if lang=='हिंदी' else 'en']:r[k] for k in TABS}} for r in matrix]
            st.dataframe(table,hide_index=True,use_container_width=True)
            st.download_button('⬇ '+tr('download'),csv_file(table),file_name='saarthi_daily_summary.csv',mime='text/csv',key='daily_export_v5')
        else:st.info(tr('nodates'))
        undated={kind:sum(r.get('_date') is None for r in recs) for kind,recs in scoped.items()}
        if any(undated.values()):
            with st.expander(tr('unknown')):
                st.dataframe([{'Report':TABS[k]['hi' if lang=='हिंदी' else 'en'],'Undated records':v} for k,v in undated.items() if v],hide_index=True)
                st.caption('Undated entries are excluded from dated charts. Add dates to the original Google Sheet to improve reporting.')
    else:st.info(tr('nodata'))

elif page=='team':
    hero(tr('team_title'),'Activity across the nine coordinators' if lang=='English' else 'नौ संयोजकों के काम की स्थिति')
    who,low,high,include,*_=filters('team')
    if loaded:
        scoped={k:filter_rows(data[k],who,low,high,include) for k in TABS}
        workers=[p for p in COORDINATORS if who in (ALL,p['en'])]
        team_records=[]
        for member in workers:
            w=member['en']
            d=[r for r in scoped['daily'] if r['_coordinator']==w]
            reg=[r for r in scoped['registration'] if r['_coordinator']==w]
            wa=[r for r in scoped['whatsapp'] if r['_coordinator']==w]
            act=[r for r in scoped['actions'] if r['_coordinator']==w]
            team_records.append({'Coordinator / संयोजक':person_name(w),
                  'Daily entries / दैनिक एंट्री':len(d),'Registration / पंजीकरण':len(reg),
                  'WA additions / नए सदस्य':stats(wa)['additions'],
                  'Unique groups / अलग ग्रुप':stats(wa)['groups'],
                  'Action records / कार्रवाई':len(act)})
        metric_cards([('Coordinators / संयोजक',len(workers)),('Report entries / एंट्री',sum(len(x) for x in scoped.values())),(tr('wa'),stats(scoped['whatsapp'])['additions'])])
        heading(tr('byworker'))
        chart=[{'Coordinator':r['Coordinator / संयोजक'],'Value':r['Daily entries / दैनिक एंट्री']+r['Registration / पंजीकरण']+r['Action records / कार्रवाई']} for r in team_records]
        if not make_chart(chart,'Coordinator','Value',horizontal=True,height=325):st.info(tr('nodata'))
        st.caption('Comparison excludes WhatsApp addition counts because people-addition totals are different units from report entries.')
        heading(tr('table'))
        st.dataframe(team_records,hide_index=True,use_container_width=True)
        st.download_button('⬇ '+tr('download'),csv_file(team_records),file_name='saarthi_coordinator_summary.csv',mime='text/csv',key='team_export_v5')
    else:st.info(tr('nodata'))

elif page=='health':
    hero(tr('health'),'Office-only diagnostic view · Nine Sheets × six reporting sections')
    metric_cards([('Readable tabs',connected if loaded else '—'),('Expected tabs',total),('Google Sheets',len(COORDINATORS)),('Undated records',sum(r.get('undated',0) for r in health))])
    if health:
        public_health=[{**x,'detail':str(x.get('detail',''))[:240]} for x in health]
        st.dataframe(public_health,hide_index=True,use_container_width=True,height=480)
    else:st.error(failure or 'No source diagnostics available.')
    with st.expander('Connection troubleshooting / कनेक्शन मदद'):
        st.markdown('''1. Streamlit Cloud → **App Settings → Secrets**: provide your current `dashboard_password` and `[gcp_service_account]`.
2. The same service account needs **Viewer** permission on each of the nine original Sheets.
3. Check the Sheets API is enabled, and the key is valid. Never put the JSON key in GitHub.
4. Select **Live Google Sheets** in Office tools; press Refresh.
5. Resolve any missing tabs before interpreting whole-constituency totals.''')

footer()
