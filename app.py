"""Manjhanpur Field Operations · V3. Reads nine original Google Sheets, no writes."""
import csv
import datetime as dt
import hmac
import html
import io
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from config import COORDINATORS, TABS, SECTION_FIELDS, FIELD_NAMES
from data_layer import (
    init_data, load_online, load_snapshots, load_sample, filter_rows, stats,
    mask_phone, normalized_booth, parse_date, to_int, display_value,
)

st.set_page_config(page_title="Manjhanpur 252 | Field Operations", page_icon="📍", layout="wide", initial_sidebar_state="expanded")
HERE = Path(__file__).resolve().parent
NOW = dt.datetime.now(ZoneInfo("Asia/Kolkata"))
LANG = {
    "English": {
        "home": "Command Center", "report":"Date-wise Report", "health":"Connection & Quality",
        "title":"Manjhanpur Field Operations", "sub":"Assembly 252 · Consolidated field reporting",
        "all":"All Coordinators", "filter":"Coordinator", "date":"Date range", "every":"All dates",
        "today":"Today", "yesterday":"Yesterday", "week":"Last 7 days", "month":"Last 30 days", "custom":"Custom range",
        "missing":"Include undated records", "search":"Search records", "booth":"Booth",
        "additions":"Reported WA additions", "groups":"Unique WA groups", "registration":"Worker registrations",
        "visited":"Booths visited", "issues":"Ground observations", "daily":"Daily tracker entries",
        "updated":"Last checked", "tabfilters":"Filters for this reporting section", "export":"Download filtered CSV",
        "undated":"Undated records", "bycoord":"Coordinator activity", "bydate":"Daily activity",
        "navigation":"Explore reports", "noresults":"No matching entries for these filters.",
    },
    "हिंदी": {
        "home": "मुख्य पृष्ठ", "report":"दिनांकवार रिपोर्ट", "health":"कनेक्शन एवं डेटा जांच",
        "title":"मंझनपुर फील्ड ऑपरेशंस", "sub":"विधानसभा 252 · संयुक्त फील्ड रिपोर्टिंग",
        "all":"सभी संयोजक", "filter":"संयोजक", "date":"तारीख का फिल्टर", "every":"सभी तारीखें",
        "today":"आज", "yesterday":"कल", "week":"पिछले 7 दिन", "month":"पिछले 30 दिन", "custom":"चुनी हुई अवधि",
        "missing":"बिना तारीख की एंट्री भी दिखाएं", "search":"रिकॉर्ड खोजें", "booth":"बूथ",
        "additions":"व्हॉट्सऐप पर जोड़े गए", "groups":"अलग व्हॉट्सऐप ग्रुप", "registration":"कार्यकर्ता पंजीकरण",
        "visited":"दौरा किए बूथ", "issues":"ग्राउंड रिपोर्ट", "daily":"दैनिक एंट्री",
        "updated":"आखिरी जांच", "tabfilters":"इस रिपोर्ट के फिल्टर", "export":"फ़िल्टर किए CSV डाउनलोड करें",
        "undated":"बिना तारीख के रिकॉर्ड", "bycoord":"संयोजक का कार्य", "bydate":"दैनिक गतिविधि",
        "navigation":"रिपोर्ट देखें", "noresults":"इन फिल्टर में कोई रिकॉर्ड नहीं मिला।",
    },
}

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Hind:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] {font-family:'DM Sans','Hind',sans-serif}
.stApp {background: #f5f7fb; color: #1a2c43}
[data-testid="stSidebar"] {background: #0e2943}
[data-testid="stSidebar"] * {color: #e4ecf4!important}
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input {color: #142a41!important}
[data-testid="stSidebar"] button {background:#244b69!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label {line-height:1.3}
.block-container{padding-top:1.3rem;max-width:1520px;padding-bottom:3rem}
.hero {background:linear-gradient(120deg,#102b45,#1d4c64);border-radius:18px;color:white;padding:26px 29px 22px;margin-bottom:15px}
.hero .eyebrow {font-size:.73rem;letter-spacing:.12em;color:#add5df;font-weight:700}
.hero h1 {font-size:2.4rem;font-weight:750;color:#fff;margin:5px 0 7px;letter-spacing:-.035em}
.hero .subtitle {font-size:.91rem;color:#cee0ea}
.portrait-card {border:1px solid #e3e9f0;background:#fff;border-radius:15px;padding:12px;min-height:260px}
.portrait-card img {width:100%;height:170px;object-fit:cover;object-position:center 23%;border-radius:10px;background:#e8eef4}
.portrait-card .person {margin-top:10px;font-size:.97rem;font-weight:750;color:#102b45}
.portrait-card .post {font-size:.76rem;color:#6d8294;margin-top:2px}
.metric-card {background:#fff;border:1px solid #e4eaf2;padding:18px 17px;border-radius:14px;min-height:116px}
.metric-card .number {font-size:30px;font-weight:750;color:#112c45;line-height:1.4}
.metric-card .label {font-size:.77rem;font-weight:650;color:#60768b}
.metric-card .foot {font-size:.7rem;color:#8a9baa}
.section-title {font-size:1.15rem;font-weight:760;color:#142d45;margin:19px 0 11px}
.nav-tile {background:#fff;border:1px solid #dce5ee;border-radius:12px;padding:15px;margin-bottom:10px}
.nav-tile strong {font-size:.88rem;color:#1b364e}
.nav-tile small {color:#75899b;display:block;margin-top:4px}
.notice {background:#e8f2fa;border-left:4px solid #2375aa;border-radius:8px;padding:14px 16px;color:#234d71;margin:13px 0}
.caps {font-size:.72rem;color:#607589;font-weight:700;letter-spacing:.075em}
[data-testid="stMetric"] {background:#fff;border:1px solid #e5eaf0;padding:13px;border-radius:13px}
</style>''', unsafe_allow_html=True)

try:
    secrets=dict(st.secrets)
except Exception:
    secrets={}
account=secrets.get("gcp_service_account")
password=str(secrets.get("dashboard_password","")).strip()

if "page_v3" not in st.session_state:
    st.session_state.page_v3="home"

# Button callbacks run before the next Streamlit render, so updating
# the radio widget's key here avoids StreamlitWidgetAlreadyInstantiatedError.
def navigate_to_page(destination: str) -> None:
    st.session_state["page_v3"] = destination
if "demo_v3" not in st.session_state:
    st.session_state.demo_v3=False

with st.sidebar:
    st.markdown("### ◈ MANJHANPUR 252")
    st.caption("MP OFFICE · FIELD OPERATIONS")
    language=st.selectbox("Language / भाषा",["English","हिंदी"],key="language_v3")
    T=LANG[language]
    st.divider()
    # LIVE is ALWAYS the default; we must not fall silently into an empty XLSX uploader.
    source_options=["🔴 Live · Original Google Sheets", "🧪 Sample preview (fictional)", "📁 Upload XLSX (offline)"]
    default_source=1 if st.session_state.demo_v3 else 0
    mode=st.radio("Data source / डेटा का स्रोत",source_options,index=default_source,key="mode_v3")
    if mode==source_options[0]:
        if account and password:st.success("Private connection configured")
        elif account:st.warning("Office password is missing")
        else:st.warning("Google access not configured")
    else:
        st.warning("PREVIEW ONLY · NOT LIVE")
    if st.button("↻ Refresh data / रीफ़्रेश",type="primary",use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.caption("Live: checks about every 60 seconds when connected")
    st.divider()
    choices=["home", *TABS.keys(), "report", "health"]
    def label(k):
        return T["home"] if k=="home" else T["report"] if k=="report" else T["health"] if k=="health" else TABS[k]["hi" if language=="हिंदी" else "en"]
    page=st.radio("Navigate / नेविगेशन",choices,format_func=label,key="page_v3")
    st.divider()
    with st.expander("Nine original Google Sheets"):
        for w in COORDINATORS:
            st.markdown(f"[{w['en']}](https://docs.google.com/spreadsheets/d/{w['id']}/edit)")

if mode==source_options[0] and account and not password:
    st.error("Safety: a private-sheet connection is configured but `dashboard_password` is missing from .streamlit/secrets.toml. Add a password before showing real field records.")

# Authorize BEFORE reading the real records.
if mode==source_options[0] and account and password:
    if not st.session_state.get("office_auth_v3",False):
        st.markdown('<div class="hero"><div class="eyebrow">MANJHANPUR 252 · OFFICE ACCESS</div><h1>Restricted live dashboard</h1><div class="subtitle">Sign in to view confidential field reports.</div></div>',unsafe_allow_html=True)
        with st.form("office_login_v3"):
            given=st.text_input("Office password / पासवर्ड",type="password")
            if st.form_submit_button("Open dashboard"):
                if hmac.compare_digest(given,password):
                    st.session_state.office_auth_v3=True;st.rerun()
                else:st.error("Incorrect password.")
        st.stop()

loaded=False
source_name="NOT CONNECTED · NO LIVE RECORDS"
last_error=None
if mode==source_options[0] and account and password:
    st_autorefresh(interval=60_000,key="live_refresh_v3")
    @st.cache_data(ttl=50,show_spinner="Reading nine Google Sheets...")
    def fetch_live(_credentials):
        return load_online(_credentials)
    try:
        data,health=fetch_live(account)
        loaded=any(h.get("ok") for h in health)
        source_name="LIVE · ORIGINAL GOOGLE SHEETS"
    except Exception as exc:
        data=init_data();health=[]
        last_error=f"{type(exc).__name__}: {exc}"
elif mode==source_options[1]:
    data,health=load_sample();loaded=True;source_name="FICTIONAL DEMONSTRATION · NOT LIVE"
elif mode==source_options[2]:
    # Upload mode is opt-in. It does not interrupt the command center.
    files=st.file_uploader("Upload any of the nine coordinator .xlsx files",type=["xlsx"],accept_multiple_files=True)
    if files:
        data,health=load_snapshots(files);loaded=True;source_name="MANUALLY UPLOADED SNAPSHOT · NOT LIVE"
    else:data=init_data();health=[];source_name="WAITING FOR XLSX UPLOAD · NOT LIVE"
else:
    data=init_data();health=[]

health_ok=sum(1 for h in health if h.get("ok"))
health_total=len(COORDINATORS)*len(TABS)
fully_connected=mode==source_options[0] and health_ok==health_total
stamp=NOW.strftime("%d %b %Y · %I:%M:%S %p IST")
if loaded:
    if mode==source_options[0] and health_ok<health_total:
        st.warning(f"Partial live data: {health_ok}/{health_total} reporting tabs readable. Totals may be incomplete.")
    elif mode==source_options[0]:
        st.success(f"● LIVE — {health_ok}/{health_total} tabs connected · checked {stamp}")
    else:st.info(f"Preview mode: {source_name}. This is not an automatic connection to Google Sheets.")
elif mode==source_options[0]:
    st.warning("● LIVE NOT CONNECTED — Dashboard is ready, but the nine private Google Sheets cannot yet be read. See the connection instructions below.")
    if last_error:st.error("Google connection error: " + last_error)

ALL="All Coordinators"
coordinator_names=[ALL]+[w["en"] for w in COORDINATORS]
def show_person(n):
    if n==ALL:return T["all"]
    if language=="हिंदी":return next((w['hi'] for w in COORDINATORS if w['en']==n),n)
    return n

def safe(x):return html.escape(str(x),quote=True)

def section(title):st.markdown(f'<div class="section-title">{safe(title)}</div>',unsafe_allow_html=True)

def hero(title,subtitle=""):
    st.markdown('<div class="hero"><div class="eyebrow">MANJHANPUR ASSEMBLY 252 · OFFICE OF MP PUSHPENDRA SAROJ</div>'
                f'<h1>{safe(title)}</h1><div class="subtitle">{safe(subtitle)}</div></div>',unsafe_allow_html=True)

def metric(label,value,foot=""):
    shown=f"{value:,}" if isinstance(value,int) else str(value)
    st.markdown(f'<div class="metric-card"><div class="label">{safe(label)}</div><div class="number">{safe(shown)}</div><div class="foot">{safe(foot)}</div></div>',unsafe_allow_html=True)

def date_filter(key):
    spans=[T['every'],T['today'],T['yesterday'],T['week'],T['month'],T['custom']]
    a,b=st.columns([1.1,1.7])
    with a:chosen=st.selectbox(T['date'],spans,key=key+'_span')
    low=high=None
    today=NOW.date()
    if chosen==T['today']:low=high=today
    elif chosen==T['yesterday']:low=high=today-dt.timedelta(days=1)
    elif chosen==T['week']:low=today-dt.timedelta(days=6);high=today
    elif chosen==T['month']:low=today-dt.timedelta(days=29);high=today
    elif chosen==T['custom']:
        with b:pick=st.date_input("From / To",value=(today-dt.timedelta(days=7),today),key=key+'_custom')
        if isinstance(pick,(tuple,list)) and len(pick)==2:low,high=pick
    include_undated=False
    if chosen!=T['every']:
        include_undated=st.checkbox(T['missing'],key=key+'_undated')
    return low,high,include_undated

def export(rows,kind):
    converted=[]
    for r in rows:
        rec={"Coordinator / संयोजक":show_person(r.get('_coordinator',''))}
        for field in SECTION_FIELDS[kind]:
            value=r.get(field,'')
            if field=='date':value=r['_date'].isoformat() if r.get('_date') else 'Undated / बिना तारीख'
            if field=='phone':value=mask_phone(value)
            if field=='booth':value=normalized_booth(value)
            if field in ('additions','team_size','followers'):value=to_int(value)
            rec[FIELD_NAMES[field][0 if language=='English' else 1]]=display_value(field,value,language)
        converted.append(rec)
    return converted

def as_csv(records):
    sink=io.StringIO()
    if not records:return ''.encode('utf-8')
    cols=list(records[0]); w=csv.DictWriter(sink,fieldnames=cols);w.writeheader();w.writerows(records)
    return sink.getvalue().encode('utf-8-sig')

def show_table(rows,kind,key):
    if not rows:st.info(T['noresults']);return
    st.dataframe(export(rows,kind),use_container_width=True,hide_index=True,height=min(520,80+len(rows)*36))
    st.download_button(T['export'],as_csv(export(rows,kind)),file_name=f'manjhanpur_{kind}_{NOW.date()}.csv',mime='text/csv',key=key)

def connection_instructions():
    with st.expander("Connect the nine ORIGINAL Google Sheets / नौ असली गूगल शीट कैसे जोड़ें",expanded=True):
        st.markdown('''**Why this is required:** The original worksheets are private. Google does not allow a local Streamlit application to read them just from their links.

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project and enable **Google Sheets API**.
2. Create a **service account** and download its JSON key (if your organization permits JSON keys).
3. Open each of the **nine original Google Sheets**, click **Share**, and give the service account's `client_email` **Viewer** permission.
4. In VS Code, create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`. Enter the account's JSON values and set `dashboard_password`.
5. Restart Streamlit and sign in with the office password. This page will change to **LIVE · ORIGINAL GOOGLE SHEETS**, with 54 reporting tabs checked.

Do **not** publish private workers' information as public CSV, and do **not** paste the JSON key into chat.''')
        st.caption('The app never writes to a Google Sheet. Every manual Refresh clears its cache; automatic updates check roughly once per minute.')

if page=="home":
    hero(T['title'],T['sub'])
    left,middle,right=st.columns([1.05,1.05,2.25],gap="medium")
    portrait1="https://assets.telegraphindia.com/telegraph/2024/Jun/1718003396_pushpendra-saroj_facebook_pushpendra-saroj-1.jpg"
    portrait2="https://www.jansatta.com/wp-content/uploads/2025/04/indrajeet-saroj.jpg"
    with left:
        st.markdown(f'<div class="portrait-card"><img src="{portrait1}" alt="Portrait of MP Pushpendra Saroj"><div class="person">MP Pushpendra Saroj</div><div class="post">Kaushambi · Lok Sabha</div></div>',unsafe_allow_html=True)
    with middle:
        st.markdown(f'<div class="portrait-card"><img src="{portrait2}" alt="Portrait of MLA Indrajeet Saroj"><div class="person">MLA Indrajeet Saroj</div><div class="post">Manjhanpur · Assembly 252</div></div>',unsafe_allow_html=True)
    with right:
        section('Office monitoring / कार्यालय मॉनिटरिंग')
        st.write('**9 coordinators · 6 report sections · 54 linked tabs**' if language=='English' else '**9 संयोजक · 6 रिपोर्ट सेक्शन · 54 जुड़े हुए टैब**')
        st.write('Select a coordinator and date range to inspect the original ground reports. Field workers continue editing their own Google Sheets.' if language=='English' else 'संयोजक और तारीख चुनकर फील्ड रिपोर्ट देखें। ग्राउंड टीम अपनी मूल गूगल शीट में ही डेटा भरती रहेगी।')
        st.caption(f'Data status: {source_name} · {stamp}')
        if loaded:st.success('Data available · view consolidated stats below')
        else:st.error('Original Google Sheets not authorized yet. Data will appear as soon as access is configured.')
    if not loaded and mode==source_options[0]:connection_instructions()
    section('Live overview / समग्र स्थिति' if loaded and mode==source_options[0] else 'Overview / समग्र स्थिति')
    # Dashboard starts with images and then the metrics, NEVER stops at an uploader.
    filter_left,filter_right=st.columns([1.4,2.4])
    with filter_left:coordinator=st.selectbox(T['filter'],coordinator_names,format_func=show_person,key='home_w')
    with filter_right:low,high,include_undated=date_filter('home_v3')
    sliced={k:filter_rows(data[k],coordinator,low,high,include_undated) for k in TABS}
    wa=sliced['whatsapp'];daily=sliced['daily']
    booths={normalized_booth(r.get('booth')) for r in daily if normalized_booth(r.get('booth'))}
    indicators=[(T['additions'],stats(wa)['additions']), (T['groups'],stats(wa)['groups']),
                (T['registration'],len(sliced['registration'])),(T['visited'],len(booths)),(T['issues'],len(sliced['actions']))]
    cols=st.columns(5)
    for col,(name,v) in zip(cols,indicators):
        with col:metric(name,v if loaded else '—','' if loaded else 'Awaiting sheet access')
    if loaded:
        if stats(wa)['undated']:
            st.caption(f'WhatsApp entries missing dates: {stats(wa)["undated"]}. Date-wise filters exclude them unless "Include undated" is checked.')
        section(T['bycoord'])
        comparisons=[]
        for w in COORDINATORS:
            name=w['en']; d=[r for r in daily if r['_coordinator']==name]
            wr=[r for r in sliced['registration'] if r['_coordinator']==name]
            wx=[r for r in wa if r['_coordinator']==name]
            comparisons.append({T['filter']:show_person(name),T['daily']:len(d),T['registration']:len(wr),T['additions']:stats(wx)['additions'],T['groups']:stats(wx)['groups']})
        st.dataframe(comparisons,use_container_width=True,hide_index=True)
    section(T['navigation'])
    tabs=list(TABS.items())
    for a,b in [tabs[i:i+2] for i in range(0,len(tabs),2)]:
        cols=st.columns(2)
        for col,(kind,meta) in zip(cols,[a,b]):
            with col:
                st.markdown(f'<div class="nav-tile"><strong>{safe(meta["hi"] if language=="हिंदी" else meta["en"])}</strong><small>{safe("Filter by coordinator, date and booth" if language=="English" else "संयोजक, तारीख व बूथ अनुसार")}</small></div>',unsafe_allow_html=True)
                st.button(
                    'Open / खोलें',
                    key='nav_'+kind,
                    use_container_width=True,
                    on_click=navigate_to_page,
                    args=(kind,),
                )

elif page in TABS:
    hero(TABS[page]['hi' if language=='हिंदी' else 'en'], 'Combined from nine original coordinator worksheets' if language=='English' else 'नौ मूल संयोजक शीट का संयुक्त डेटा')
    if not loaded:
        st.info('No live records available yet. Connect Google Sheet access using the instructions on the Command Center.' if language=='English' else 'लाइव डेटा के लिए मुख्य पृष्ठ पर गूगल शीट कनेक्शन पूरा करें।')
        connection_instructions()
    section(T['tabfilters'])
    chosen=st.selectbox(T['filter'],coordinator_names,format_func=show_person,key='worker_'+page)
    low,high,include_undated=date_filter('tab_'+page)
    x,y=st.columns([1.1,1.9])
    with x:
        booth_list=sorted({normalized_booth(r.get('booth')) for r in data[page] if normalized_booth(r.get('booth'))})
        pick=st.selectbox(T['booth'],['All booths']+booth_list,key='booth_'+page)
    with y:needle=st.text_input(T['search'],placeholder='Search / खोजें',key='search_'+page)
    selected=filter_rows(data[page],chosen,low,high,include_undated,query=needle,booth=pick)
    tiles=st.columns(4)
    for col,(lab,v) in zip(tiles,[("Matching entries",len(selected)),(T['undated'],stats(selected)['undated']),
                                  (T['groups'] if page=='whatsapp' else T['visited'], stats(selected)['groups'] if page=='whatsapp' else len({normalized_booth(r.get('booth')) for r in selected if normalized_booth(r.get('booth'))})),
                                  (T['additions'] if page=='whatsapp' else 'Coordinator sheets', stats(selected)['additions'] if page=='whatsapp' else len({r['_coordinator'] for r in selected}))]):
        with col:metric(lab,v if loaded else '—')
    if page=='whatsapp':
        st.caption('A WhatsApp group is counted once by invite link (or normalized name); all separate daily addition rows are summed. This is not a verified unique-person count.')
    show_table(selected,page,'export_'+page)
    counts={}
    for r in selected:
        d=r.get('_date');key=d.isoformat() if d else None
        if key:counts[key]=counts.get(key,0)+(r.get('additions',0) if page=='whatsapp' else 1)
    if counts:
        section(T['bydate']);st.bar_chart([{'Date':k,'Amount':counts[k]} for k in sorted(counts)],x='Date',y='Amount',color='#2774a4')
    elif selected:
        st.warning('No dated records in this selection. Add an Entry Date column to the original reporting tab for accurate date-wise calculations.')

elif page=='report':
    hero(T['report'], 'Daily reporting across six sections and all nine coordinators' if language=='English' else 'नौ संयोजकों और छह सेक्शन की दिनांकवार रिपोर्ट')
    if not loaded:connection_instructions()
    chosen=st.selectbox(T['filter'],coordinator_names,format_func=show_person,key='report_worker')
    low,high,include_undated=date_filter('report_v3')
    report=[]
    for kind,meta in TABS.items():
        rows=filter_rows(data[kind],chosen,low,high,include_undated)
        report.append({"Section":meta['hi' if language=='हिंदी' else 'en'],"Records":len(rows),"Undated":stats(rows)['undated'],"Reported additions":stats(rows)['additions'] if kind=='whatsapp' else 0})
    st.dataframe(report,hide_index=True,use_container_width=True)
    st.download_button(T['export'],as_csv(report),'manjhanpur_section_summary.csv','text/csv')
    dated={}
    for kind in TABS:
        for row in filter_rows(data[kind],chosen,low,high,include_undated):
            if row['_date']:
                day=row['_date'].isoformat();dated.setdefault(day,{'Date':day,**{k:0 for k in TABS}})
                dated[day][kind]+=row.get('additions',0) if kind=='whatsapp' else 1
    if dated:
        section(T['bydate']);st.dataframe([dated[k] for k in sorted(dated)],hide_index=True,use_container_width=True)
        st.download_button('Download dated summary',as_csv([dated[k] for k in sorted(dated)]),'manjhanpur_dates.csv','text/csv')
    else:st.info('No dated records match this period. Undated rows cannot be allocated to a date.')

else:
    hero(T['health'], 'Audit every original worksheet connection' if language=='English' else 'हर मूल वर्कशीट के कनेक्शन की जांच')
    a,b,c=st.columns(3)
    with a:metric('Readable tabs',health_ok if loaded else '—')
    with b:metric('Expected tabs',health_total)
    with c:metric('Source workbooks',len(COORDINATORS))
    if health:st.dataframe(health,hide_index=True,use_container_width=True)
    else:connection_instructions()
    st.caption('Data source IDs are fixed in config.py. We never overwrite original workbooks. Access must be granted for all nine private Sheets.')

st.divider()
st.caption('Manjhanpur 252 · Read-only office reporting. Original Google Sheets are the source of truth. Blank template serials are excluded; missing entry dates are not guessed. Demo/upload modes are NOT live.')
