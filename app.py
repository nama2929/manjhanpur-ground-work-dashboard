"""Saarthi Analytics | Manjhanpur 252 Constituency Operations V5.4.1 Solar Light — table-first.
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
from solar_layer import SOLAR_SHEET_URL, load_solar_online, solar_summary, solar_villages, solar_filter, masked_phone

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "saarthi-logo.png"
FAVICON = ROOT / "assets" / "saarthi-favicon.png"
LOGO_URI = 'data:image/png;base64,' + base64.b64encode(LOGO.read_bytes()).decode('ascii')
st.set_page_config(
    page_title="Saarthi Analytics | Manjhanpur 252",
    page_icon=str(FAVICON), layout="wide", initial_sidebar_state="auto",
)
try:
    st.logo(str(LOGO), icon_image=str(FAVICON), size="large")
except (AttributeError, TypeError):
    pass

NOW = dt.datetime.now(ZoneInfo("Asia/Kolkata"))
ALL = "All Coordinators"
PAGES = ["home", "reports", "dates", "team"]
SOLAR_LABEL = {"English":"Solar Light Verification", "हिंदी":"सोलर लाइट सत्यापन"}
# Stable local portraits from the office dashboard's previously shared visual reference.
# Avoid external image hotlink failures on iPhones and other browsers.
def local_img_uri(name: str) -> str:
    path = ROOT / 'assets' / name
    return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')

PORTRAIT_MP = local_img_uri('pushpendra-saroj.jpg')
PORTRAIT_MLA = local_img_uri('indrajeet-saroj.jpg')
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
        'registrations':'Youth worker registrations','booths':'Booths visited','observations':'Actionable records',
        'entries':'Total report entries','nodata':'No records match the current filters.',
        'nodates':'No dated records are available for this selection.', 'unknown':'Entries without dates',
        'team_title':'Coordinator Overview', 'quick':'Open a report', 'office':'Office view',
        'refresh':'Refresh data','login':'Office sign in','data':'Source', 'source':'Connection',
        'metrics':'At a glance','records':'Records','status':'Current reporting status',
        'scope':'Keep these filters across reports','reset':'Reset filters','readable':'Full records',
        'spreadsheet':'Table view','page':'Page','of':'of','per_page':'Records per page',
        'village_all':'All panchayats', 'active':'Currently viewing',
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
        'registrations':'युवा कार्यकर्ता पंजीकरण','booths':'दौरे वाले बूथ','observations':'कार्रवाई योग्य रिकॉर्ड',
        'entries':'कुल रिपोर्ट एंट्री','nodata':'चुने हुए फिल्टर में रिकॉर्ड नहीं मिले।',
        'nodates':'चुनी हुई अवधि में दिनांकित रिकॉर्ड नहीं हैं।','unknown':'बिना तारीख के रिकॉर्ड',
        'team_title':'संयोजक सारांश','quick':'रिपोर्ट खोलें','office':'कार्यालय दृश्य',
        'refresh':'डेटा रीफ़्रेश','login':'कार्यालय लॉगिन','data':'डेटा स्रोत','source':'कनेक्शन',
        'metrics':'एक नज़र में','records':'रिकॉर्ड','status':'मौजूदा रिपोर्टिंग स्थिति',
        'scope':'ये फ़िल्टर सभी रिपोर्ट में लागू रहेंगे','reset':'फ़िल्टर हटाएँ','readable':'पूरा रिकॉर्ड पढ़ें',
        'spreadsheet':'तालिका देखें','page':'पृष्ठ','of':'में से','per_page':'प्रति पृष्ठ रिकॉर्ड',
        'village_all':'सभी पंचायत','active':'अभी देख रहे हैं',
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

/* V5.1 / a reading-first, touch-friendly interface on all screen sizes. */
[data-testid="stToolbar"],[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],#MainMenu{display:none!important}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stStatusWidget"]{display:none!important}
[data-testid="stMainBlockContainer"]{min-width:0!important}
[data-testid="stDataFrame"]{max-width:100%;overflow-x:auto}
.person img{display:block;object-fit:cover}
@media(min-width:701px) and (max-width:1024px){
 .block-container{padding:1.1rem 1.15rem 3rem!important}
 .people-grid{gap:10px}
 .person{gap:10px;padding:10px}
 .person img{width:82px;height:96px}
 .person strong{font-size:.88rem}
 .brand-right{white-space:normal;max-width:110px}
}
@media(max-width:700px){
 html,body,.stApp{overflow-x:hidden!important}
 .block-container{padding:.48rem .85rem 4rem!important}
 .brand-shell{padding:9px 10px;gap:6px;margin:2px 0 11px;border-radius:12px}
 .brand-logo{height:45px;width:45px}
 .brand-title{font-size:1rem;letter-spacing:-.03em}
 .brand-tag{font-size:.57rem;line-height:1.2;letter-spacing:.01em;padding-top:3px}
 .brand-right{display:none}
 .hero{padding:16px 14px;margin:9px 0 12px}
 .hero h1{font-size:1.47rem;line-height:1.14;margin:7px 0}
 .hero p{font-size:.79rem;line-height:1.4}
 .hero-eyebrow{font-size:.61rem}
 .people-grid{display:grid;grid-template-columns:1fr;gap:8px;margin-bottom:12px}
 .person{display:flex;flex-direction:row;text-align:left;gap:13px;padding:10px 12px;border-radius:14px;min-height:0}
 .person img{width:77px;height:85px;flex:0 0 77px;object-position:50% 23%;border-radius:9px}
 .person>div{flex:1;min-width:0}
 .person small{font-size:.63rem;padding-top:0;line-height:1.4}
 .person strong{font-size:.87rem;line-height:1.3;margin-top:2px}
 .person span{font-size:.71rem;line-height:1.3;padding-top:4px}
 .section-head{font-size:1.05rem;margin:13px 0 8px}
 .source-state{font-size:.73rem;gap:5px;margin:4px 0 7px;line-height:1.4}
 .state-chip{padding:4px 8px}
 .kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
 .kpi{padding:13px 11px;min-height:94px}
 .kpi-value{font-size:1.45rem}
 .kpi-label{font-size:.68rem}
 .stButton>button,div[data-testid="stDownloadButton"]>button{min-height:48px!important}
 [data-testid="stSelectbox"] label{font-size:.77rem!important}
 [data-testid="stHorizontalBlock"]{row-gap:.35rem!important}
 [data-testid="stTable"],[data-testid="stDataFrame"]{width:100%;overflow:auto}
}
@media(max-width:375px){
 .person img{width:64px;height:78px;flex-basis:64px}
 .person strong{font-size:.82rem}
 .brand-tag{font-size:.53rem}
 .kpi-label{font-size:.65rem}
}

/* V5.2 UX refinement: preserve the Saarthi palette; improve reading and navigation. */
.scope-hint{font-size:.77rem;color:#766b61;background:#fff8ef;border-left:3px solid #c68155;border-radius:7px;padding:7px 10px;margin:6px 0 12px}
.scope-chip{display:inline-block;border-radius:100px;background:#f9ebdf;color:#8b4929;padding:5px 10px;font-weight:750;font-size:.76rem;border:1px solid #e9ccba;margin:4px 0 9px}
.record-card{background:#fffdfb;border:1px solid #e7dfd4;border-left:3px solid #c1774d;border-radius:16px;padding:17px 18px;margin:10px 0;box-shadow:0 5px 18px rgba(47,41,36,.025);min-width:0;max-width:100%}
.record-card .record-index{font-size:.72rem;letter-spacing:.11em;color:#ab643e;font-weight:800;text-transform:uppercase}
.record-card .record-title{font-weight:850;font-size:1.06rem;line-height:1.55;color:#28394a;margin:6px 0 9px;overflow-wrap:anywhere;white-space:pre-wrap}
.record-meta{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0 14px}
.record-meta .meta-pill{display:inline-flex;padding:4px 9px;color:#485c6b;background:#f6f4f1;border:1px solid #e8e1d8;border-radius:100px;font-size:.72rem;font-weight:700;overflow-wrap:anywhere}
.record-info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px 16px}
.record-field{min-width:0}
.record-field.is-long{grid-column:1/-1;padding:11px 13px;border-radius:11px;background:#fcf6f0}
.record-field .record-label{color:#a25c35;font-size:.72rem;font-weight:800;line-height:1.5;margin-bottom:3px}
.record-field .record-value{color:#2c3d4a;font-size:.91rem;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}
.record-view-explainer{font-size:.78rem;color:#667a89;line-height:1.55;padding:8px 0}
.stButton>button:focus-visible,[data-baseweb="select"]:focus-within{outline:3px solid #da9b75!important;outline-offset:2px!important}
@media(max-width:700px){
 .record-card{padding:14px 12px;border-radius:13px;margin:8px 0}
 .record-info-grid{grid-template-columns:1fr;gap:9px}
 .record-field.is-long{grid-column:auto;padding:11px 10px}
 .record-card .record-title{font-size:1rem}
 .record-field .record-value{font-size:.87rem;line-height:1.85}
 .scope-hint{line-height:1.5;font-size:.75rem}
}
/* V5.3: refined full-text tables, not individually stacked record cards. */
.sa-table-note{font-size:.83rem;line-height:1.6;color:#596d7d;margin:5px 0 12px}
.sa-table-shell{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #e6ddd2;border-radius:15px;background:#fff;box-shadow:0 4px 16px rgba(47,41,36,.02);margin:7px 0 14px}
.sa-wrap-table{border-collapse:separate;border-spacing:0;width:100%;min-width:800px;table-layout:fixed;font-size:.85rem;color:#2b3d4c}
.sa-wrap-table thead th{position:sticky;top:0;z-index:1;background:#f5ede6;color:#70482e;font-weight:800;font-size:.77rem;text-align:left;letter-spacing:.005em;padding:12px 13px;border-bottom:1px solid #e2d5c8;vertical-align:middle}
.sa-wrap-table td{padding:13px 13px;vertical-align:top;line-height:1.75;border-bottom:1px solid #eee8e1;white-space:pre-wrap;overflow-wrap:anywhere;word-break:normal;hyphens:auto}
.sa-wrap-table tbody tr:nth-child(even){background:#fdfaf6}
.sa-wrap-table tbody tr:hover{background:#fff4e9}
.sa-wrap-table tbody tr:last-child td{border-bottom:0}
.sa-wrap-table th.sa-long,.sa-wrap-table td.sa-long{width:29%;min-width:210px}
.sa-wrap-table th.sa-small,.sa-wrap-table td.sa-small{width:9%}
.sa-wrap-table th.sa-meta,.sa-wrap-table td.sa-meta{width:15%}
.sa-table-shell:focus-visible{outline:3px solid #c98652;outline-offset:3px}
.sa-cell-quiet{font-size:.72rem;color:#73808a;line-height:1.55}
.sa-cell-strong{font-weight:750;color:#324456}
.sa-table-mobile{display:none}
.sa-wrap-table.sa-all-fields{min-width:1500px;table-layout:auto}
.sa-wrap-table.sa-all-fields th.sa-long,.sa-wrap-table.sa-all-fields td.sa-long{min-width:290px;max-width:460px}
.sa-table-counter{color:#5a6e7b;font-size:.83rem;font-weight:700;padding:8px 0 4px}
@media(max-width:700px){
 .sa-table-desktop{display:none!important}
 .sa-table-mobile{display:block}
 .sa-table-mobile .sa-wrap-table{min-width:0;width:100%;table-layout:fixed;font-size:.78rem}
 .sa-table-mobile th.sa-long,.sa-table-mobile td.sa-long{width:67%;min-width:0}
 .sa-table-mobile th.sa-meta,.sa-table-mobile td.sa-meta{width:33%;min-width:0}
 .sa-wrap-table thead th{font-size:.72rem;padding:9px 10px}
 .sa-wrap-table td{padding:10px;line-height:1.7}
 .sa-wrap-table th.sa-long,.sa-wrap-table td.sa-long{width:34%;min-width:150px}
 .sa-wrap-table th.sa-meta,.sa-wrap-table td.sa-meta{width:32%;min-width:135px}
 .sa-table-note{font-size:.76rem}
 .sa-detail-title{font-weight:800;color:#a35d36;display:block;margin:0 0 3px}
 .sa-mobile-details{display:grid;gap:11px}
 .sa-detail-text{display:block;white-space:pre-wrap;overflow-wrap:anywhere;color:#273846}
}

/* V5.3: direct report buttons and high-contrast selected state. */
.stMain .stButton > button[kind="primary"],
.stMain button[data-testid="stBaseButton-primary"]{
 background:#a95127!important;color:#fff!important;border:2px solid #a95127!important;
 box-shadow:0 3px 10px rgba(120,67,37,.14)!important;
}
.stMain .stButton > button[kind="primary"]:hover,
.stMain button[data-testid="stBaseButton-primary"]:hover{background:#863d1f!important;color:white!important}
.stMain .stButton > button{
 white-space:normal!important;overflow-wrap:anywhere!important;
 text-align:center!important;line-height:1.35!important;min-height:53px!important;
}
.sa-nav-label{font-size:.81rem;font-weight:800;color:#786354;margin:10px 0 6px;letter-spacing:.01em}
.sa-nav-help{font-size:.78rem;color:#73808a;margin:4px 0 10px;line-height:1.5}
.sa-selected-report{border-left:4px solid #b96532;background:#fff8f0;border-radius:9px;
 padding:9px 12px;font-weight:800;color:#8b4826;margin:12px 0 7px}
@media(max-width:700px){
 .stMain .stButton > button{min-height:55px!important;font-size:.83rem!important;padding:.48rem .30rem!important}
 .sa-nav-label{font-size:.76rem;margin:7px 0 4px}
 .sa-nav-help{font-size:.7rem}
}

/* V5.4: shared solar verification table inherits the Saarthi cream/saffron identity. */
.solar-progress-track{background:#f4e9dd;border-radius:99px;height:14px;overflow:hidden;margin:10px 0 16px}
.solar-progress-fill{height:100%;background:#43867b;border-radius:99px}
.solar-note{background:#fff6eb;color:#705037;border:1px solid #ead5bc;border-radius:12px;padding:11px 14px;font-size:.83rem;line-height:1.65;margin:10px 0}
.solar-table .sa-wrap-table{min-width:750px}
.solar-table .sa-wrap-table th:nth-child(2),.solar-table .sa-wrap-table td:nth-child(2){width:21%}
.solar-table .sa-wrap-table th:nth-child(3),.solar-table .sa-wrap-table td:nth-child(3){width:33%}
.solar-done{color:#267160;font-weight:800}
.solar-open{color:#9a5c38;font-weight:700}
@media(max-width:700px){.solar-table .sa-wrap-table{min-width:0}.solar-table .sa-table-desktop{display:none}.solar-table .sa-table-mobile{display:block}}

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

# Worker Registration column L records when a person became an SP worker,
# not the date the coordinator typed or submitted this registration.
REG_JOIN_LABEL = {
    'English': 'Date joined Samajwadi Party',
    'हिंदी': 'समाजवादी पार्टी से जुड़ने की तारीख',
}
REG_TREND_LABEL = {
    'English': 'Youth workers joined the Samajwadi Party — by joining date',
    'हिंदी': 'समाजवादी पार्टी से जुड़ने वाले युवा कार्यकर्ता — जुड़ने की तारीख अनुसार',
}
REG_DATE_NOTE = {
    'English': ('The date in this register means when the person became a Samajwadi Party worker, '
                'NOT when a coordinator entered their details. Date filters here use joining dates.'),
    'हिंदी': ('इस रजिस्टर की तारीख वह दिन है जब व्यक्ति समाजवादी पार्टी का कार्यकर्ता बना था, '
              'न कि डेटा शीट में भरने की तारीख। यहाँ तारीख का फ़िल्टर जुड़ने की तारीख पर लागू होता है।'),
}

def field_label(kind, field):
    if kind == 'registration' and field == 'date':
        return REG_JOIN_LABEL[lang]
    return FIELD_NAMES[field][0 if lang == 'English' else 1]

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
            row[field_label(kind,field)]=val
        result.append(row)
    return result

def _record_title(raw, kind):
    for field in ({'actions':['issue','panchayat'],'daily':['name','panchayat'],
                   'registration':['name','panchayat'],'whatsapp':['group','panchayat'],
                   'booth':['name','panchayat'],'social':['name','panchayat']}[kind]):
        text=str(raw.get(field,'') or '').strip()
        if text:
            return display_value(field,text,lang)
    return TABS[kind]['hi' if lang=='हिंदी' else 'en']


def readable_record_card(raw, kind, n):
    """HTML-escaped, fully wrapping, privacy-masked record for the MP's reading view."""
    friendly=public_rows([raw],kind)[0]
    long_fields={'issue','action','remarks','content'}
    long_labels={FIELD_NAMES[f][0 if lang=='English' else 1] for f in long_fields}
    skip_labels={tr('worker'),FIELD_NAMES['date'][0 if lang=='English' else 1],
                 FIELD_NAMES['booth'][0 if lang=='English' else 1]}
    title=_record_title(raw,kind)
    date=(raw.get('_date').isoformat() if raw.get('_date') else ('Undated' if lang=='English' else 'बिना तारीख'))
    booth=normalized_booth(raw.get('booth',''))
    badges=[person_name(raw.get('_coordinator','')),date]
    if booth: badges.append(('Booth ' if lang=='English' else 'बूथ ')+booth)
    badges_html=''.join(f'<span class="meta-pill">{esc(v)}</span>' for v in badges)
    cells=[]
    for label,val in friendly.items():
        if label in skip_labels or val in ('',None,'—'):
            continue
        content=esc(val)
        long=' is-long' if label in long_labels or len(str(val))>100 else ''
        cells.append(f'<div class="record-field{long}"><div class="record-label">{esc(label)}</div>'
                     f'<div class="record-value">{content}</div></div>')
    return (f'<article class="record-card"><div class="record-index">'
            f'{"Record" if lang=="English" else "रिकॉर्ड"} {n}</div>'
            f'<div class="record-title">{esc(title)}</div>'
            f'<div class="record-meta">{badges_html}</div>'
            f'<div class="record-info-grid">{"".join(cells)}</div></article>')


def _table_label(field,kind=None):
    """Translate a source field name without changing the stored record."""
    return field_label(kind,field) if kind == 'registration' and field == 'date' else FIELD_NAMES[field][0 if lang == 'English' else 1]


def _wrapped_table_html(records, kind, all_columns=False, mobile=False):
    """Make a real HTML table with UNTRUNCATED, safely escaped text.

    Phone fields are masked by public_rows; WhatsApp invite URLs stay hidden.
    The mobile projection retains the primary text and context in three columns.
    """
    friendly = public_rows(records, kind)
    if not friendly:
        return ''
    if mobile and not all_columns:
        mobile_primary = {
            'actions':'issue','daily':'name','registration':'name',
            'whatsapp':'group','booth':'name','social':'name',
        }[kind]
        mobile_secondary = {
            'actions':['action'], 'daily':['remarks'],
            'registration':['role','status'], 'whatsapp':['additions','status'],
            'booth':['role','status'], 'social':['platform','followers','content'],
        }[kind]
        labels = [('location','Coordinator · Booth / संयोजक · बूथ'),
                  ('details','Record details / रिकॉर्ड विवरण')]
    else:
        core = {
            'actions':['date','panchayat','booth','issue','action','type'],
            'daily':['date','panchayat','booth','name','remarks'],
            'registration':['date','panchayat','booth','name','role','status'],
            'whatsapp':['date','panchayat','booth','group','additions','status'],
            'booth':['date','panchayat','booth','name','role','status'],
            'social':['date','panchayat','name','platform','followers','content'],
        }[kind]
        if all_columns:
            core=list(SECTION_FIELDS[kind])
        labels=[('coordinator',tr('worker'))]+[(f,_table_label(f,kind)) for f in core]

    heading_html=''.join(
        f'<th scope="col" class="{("sa-long" if key in ("issue","action","remarks","content","details") else "sa-meta" if key in ("coordinator","location","name","panchayat") else "sa-small")}">{esc(label)}</th>'
        for key,label in labels
    )
    out=[]
    for row in friendly:
        if mobile and not all_columns:
            meta_parts=[f'<span class="sa-cell-strong">{esc(row.get(tr("worker"),""))}</span>']
            for field in ('date','panchayat','booth'):
                val=row.get(_table_label(field,kind),'')
                if val not in ('',None,'—'):
                    meta_parts.append(f'<span class="sa-cell-quiet">{esc(_table_label(field,kind))}: {esc(val)}</span>')
            detail_fields=[mobile_primary]+mobile_secondary
            details=[]
            for f in detail_fields:
                value=row.get(_table_label(f,kind),'')
                if value in ('',None,'—'):continue
                details.append(f'<span class="sa-cell-quiet sa-detail-title">{esc(_table_label(f,kind))}</span>'
                               f'<span class="sa-detail-text">{esc(value)}</span>')
            values={'location':'\n'.join(meta_parts),
                    'details':'<div class="sa-mobile-details">'+''.join(details)+'</div>'}
            # All values inside HTML are individually escaped.
            data=[values.get(k,'') for k,_ in labels]
        else:
            data=[esc(row.get(tr('worker'),'')) if key=='coordinator'
                  else esc(row.get(_table_label(key,kind),'')) for key,_ in labels]
        out.append('<tr>'+''.join(
            f'<td class="{("sa-long" if key in ("issue","action","remarks","content","details") else "sa-meta" if key in ("coordinator","location","name","panchayat") else "sa-small")}">{val}</td>'
            for (key,_),val in zip(labels,data)
        )+'</tr>')
    extra='sa-all-fields' if all_columns else ''
    position='sa-table-all' if all_columns else ('sa-table-mobile' if mobile else 'sa-table-desktop')
    caption=('Detailed reporting records / विस्तृत रिपोर्ट रिकॉर्ड')
    return (f'<div class="sa-table-shell {position}" role="region" tabindex="0" aria-label="{esc(caption)}">'
            f'<table class="sa-wrap-table {extra}"><thead><tr>{heading_html}</tr></thead>'
            f'<tbody>{"".join(out)}</tbody></table></div>')


def table_export(rows,kind,key):
    """One primary, fully wrapped TABLE. Never force a record-by-record card view."""
    total=len(rows)
    st.markdown(f'<div class="sa-table-counter">{total:,} '
                + ('matching records' if lang=='English' else 'मिलते हुए रिकॉर्ड') + '</div>',
                unsafe_allow_html=True)
    if not rows:
        st.info(tr('nodata'))
        return
    st.markdown('<div class="sa-table-note">'+esc(
        'Records appear in a table with complete, wrapped text. Use filters above to narrow results.'
        if lang=='English' else 'रिकॉर्ड तालिका में पूरे टेक्स्ट के साथ दिखाई देंगे। ऊपर दिए फिल्टर से रिकॉर्ड चुनें।'
    )+'</div>',unsafe_allow_html=True)
    left,right=st.columns([1,1],gap='small')
    with left:
        page_size=st.selectbox('Rows per page / प्रति पृष्ठ रिकॉर्ड',[10,20,50],index=0,key=f'table_size_{kind}')
    with right:
        all_columns=st.checkbox('All columns / सभी कॉलम',value=False,key=f'table_all_columns_{kind}',
                                help='Reveal every source field. Wide tables can scroll horizontally.')
    pages=max(1,(total+page_size-1)//page_size)
    page_key=f'table_page_{kind}'
    # Clamp before the widget is created; Streamlit forbids post-render widget writes.
    if st.session_state.get(page_key,1) not in range(1,pages+1):
        st.session_state[page_key]=1
    if pages>1:
        current=st.selectbox(tr('page'),list(range(1,pages+1)),
                             format_func=lambda n:f'{n} {tr("of")} {pages}',key=page_key)
    else:
        current=1
    first=(current-1)*page_size
    batch=rows[first:first+page_size]
    if all_columns:
        st.markdown(_wrapped_table_html(batch,kind,all_columns=True),unsafe_allow_html=True)
    else:
        st.markdown(_wrapped_table_html(batch,kind,mobile=False),unsafe_allow_html=True)
        st.markdown(_wrapped_table_html(batch,kind,mobile=True),unsafe_allow_html=True)
    st.caption(('Showing' if lang=='English' else 'दिखाए गए') +f' {first+1}–{min(total,first+page_size)} / {total}.'+
               (' Scroll sideways only if needed.' if lang=='English' else ' आवश्यकता हो तो दाएँ-बाएँ स्क्रॉल करें।'))
    # Export all filtered records, not just the currently visible page.
    st.download_button('⬇ '+tr('download'),csv_file(public_rows(rows,kind)),
                       file_name=f'saarthi_manjhanpur_{kind}_{NOW.date()}.csv',mime='text/csv',key=key)


def _solar_table(rows, lang, narrow=False):
    """Escaped, wrapped HTML table. No single-record cards; phones get 2 columns."""
    en = lang == 'English'
    headers=(['Location / स्थल','Verification / सत्यापन'] if narrow else
             (['No.','Village','Installation site','Contact','Status'] if en else
              ['क्र.','ग्राम','स्थल का नाम','संपर्क नाम','स्थिति']))
    head=''.join('<th scope="col">'+esc(x)+'</th>' for x in headers)
    cells=[]
    for r in rows:
        status=('Done' if r['done'] else 'Not marked Done') if en else ('पूर्ण (Done)' if r['done'] else 'Done दर्ज नहीं')
        status_html=f'<span class="{"solar-done" if r["done"] else "solar-open"}">{esc(status)}</span>'
        if narrow:
            first=('<strong>'+esc(r['village'])+'</strong><br>'+esc(r['site'])+'<br><small>#'+esc(r['serial'])+'</small>')
            second=(status_html+'<br><small>'+esc(r['contact'])+'</small>')
            values=[first,second]
        else:
            values=[esc(r['serial']),esc(r['village']),esc(r['site']),esc(r['contact']),status_html]
        cells.append('<tr>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
    mobile='sa-table-mobile' if narrow else 'sa-table-desktop'
    return ('<div class="sa-table-shell '+mobile+' solar-table" role="region" tabindex="0" '
            'aria-label="Solar light verification table"><table class="sa-wrap-table"><thead><tr>'+head+
            '</tr></thead><tbody>'+''.join(cells)+'</tbody></table></div>')


def solar_report(rows, accessible, error):
    """Show the shared team's verification TABLE first, followed by visual analysis."""
    hero(SOLAR_LABEL[lang],
         'Shared team verification — based on the single original Solar Light Google Sheet.' if lang=='English'
         else 'पूरी टीम की साझा सत्यापन रिपोर्ट — मूल गूगल शीट के आधार पर।')
    st.link_button('↗ '+('Open original Google Sheet' if lang=='English' else 'मूल गूगल शीट खोलें'),
                   SOLAR_SHEET_URL, use_container_width=False)
    if not accessible:
        st.warning(('Solar Light source is not connected. Share the Solar Light spreadsheet with the '
                    'existing service-account email as Viewer, then select Refresh data. The other nine '
                    'coordinator sheets will continue working.') if lang=='English' else
                   'सोलर शीट कनेक्ट नहीं है। मौजूदा सर्विस अकाउंट को इस शीट पर Viewer एक्सेस दें और रीफ़्रेश करें।')
        if error:st.caption(str(error)[:240])
        return

    # Filters are followed immediately by the table (not charts or KPI cards).
    st.markdown('### '+('Find verification records' if lang=='English' else 'सत्यापन रिकॉर्ड खोजें'))
    a,b=st.columns(2,gap='small')
    villages=sorted({r['village'] for r in rows if r['village']})
    with a:
        village=st.selectbox('Village / ग्राम',['All villages']+villages,
                             format_func=lambda s:('सभी गांव' if s=='All villages' and lang=='हिंदी' else s),
                             key='solar_village_v54')
    with b:
        status=st.selectbox('Verification status / सत्यापन स्थिति',['All','Done','Not marked Done'],
                            format_func=lambda s:{'All':'सभी','Done':'पूर्ण (Done)','Not marked Done':'Done दर्ज नहीं'}[s] if lang=='हिंदी' else s,
                            key='solar_status_v54')
    search=st.text_input('Search serial, village, site or name / क्रमांक, गांव, स्थल या नाम खोजें',
                         key='solar_search_v54',placeholder='e.g. बरौला, school, 101')
    filtered=solar_filter(rows,village,status,search)
    filtered_summary=solar_summary(filtered)
    heading('📋 '+('Verification records' if lang=='English' else 'सत्यापन रिकॉर्ड तालिका'))
    st.caption((f'{filtered_summary["total"]} matching locations · {filtered_summary["done"]} marked Done'
               if lang=='English' else
               f'{filtered_summary["total"]} स्थल मिले · {filtered_summary["done"]} Done दर्ज'))

    if not filtered:
        st.info(tr('nodata'))
    else:
        controls_1,controls_2=st.columns([1.1,1.6],gap='small')
        with controls_1:
            psize=st.selectbox('Rows per page / प्रति पृष्ठ',[10,20,50],index=1,key='solar_page_size_v54')
        pages=max(1,(len(filtered)+psize-1)//psize)
        if st.session_state.get('solar_page_v54',1)>pages:
            st.session_state['solar_page_v54']=1
        with controls_2:
            current_solar_slice=(st.selectbox(tr('page'),list(range(1,pages+1)),
                                format_func=lambda x:f'{x} / {pages}',key='solar_page_v54')
                                if pages>1 else 1)
        batch=filtered[(current_solar_slice-1)*psize:current_solar_slice*psize]
        # Two responsive presentations of the same records: a full desktop table
        # and a mobile two-column table; CSS hides whichever does not fit.
        st.markdown(_solar_table(batch,lang,False),unsafe_allow_html=True)
        st.markdown(_solar_table(batch,lang,True),unsafe_allow_html=True)
        st.caption(f'{(current_solar_slice-1)*psize+1}–{min(current_solar_slice*psize,len(filtered))} / {len(filtered)}')
        export=[{'Serial / क्रमांक':r['serial'],'Village / ग्राम':r['village'],'Site / स्थल':r['site'],
                 'Contact / नाम':r['contact'],'Phone (masked) / मोबाइल':masked_phone(r['phone']),
                 'Status / स्थिति':('Done' if r['done'] else 'Not marked Done')}
                for r in filtered]
        st.download_button('⬇ '+tr('download'),csv_file(export),
                           file_name='saarthi_solar_light_verification.csv',mime='text/csv',key='solar_export_v54')

    st.divider()
    heading('📊 '+('Verification progress & charts' if lang=='English' else 'सत्यापन प्रगति और ग्राफ'))
    # Totals reflect the current village/status/search filters, for consistency
    # with the table immediately above. Provide the overall scale separately.
    metric_cards([
        ('Locations / स्थल',filtered_summary['total']),
        ('Marked Done / पूर्ण',filtered_summary['done']),
        ('Not marked Done / शेष',filtered_summary['unmarked']),
        ('Done percentage / पूर्ण %',str(filtered_summary['pct'])+'%'),
    ])
    st.markdown('<div class="solar-progress-track" role="progressbar" aria-valuenow="'+esc(filtered_summary['pct'])+'" '
                'aria-valuemin="0" aria-valuemax="100"><div class="solar-progress-fill" style="width:'+esc(filtered_summary['pct'])+'%"></div></div>',
                unsafe_allow_html=True)
    if filtered:
        st.markdown('#### '+('Verification status' if lang=='English' else 'सत्यापन की स्थिति'))
        status_rows=[{'Status': 'Done' if lang=='English' else 'पूर्ण', 'Count':filtered_summary['done']},
                     {'Status': 'Not marked Done' if lang=='English' else 'शेष', 'Count':filtered_summary['unmarked']}]
        chart=alt.Chart(pd.DataFrame(status_rows)).mark_bar(cornerRadiusEnd=5).encode(
            x=alt.X('Count:Q',title=None), y=alt.Y('Status:N',title=None,sort=None),
            color=alt.Color('Status:N',scale=alt.Scale(domain=[v['Status'] for v in status_rows],range=['#43867b','#c89168']),legend=None),
            tooltip=['Status','Count']).properties(height=115)
        st.altair_chart(chart,use_container_width=True)
        village_summary=solar_villages(filtered)
        if village_summary:
            heading('Top villages by listed locations / ग्रामवार स्थल')
            top=village_summary[:12]
            graph=alt.Chart(pd.DataFrame([{'Village':r['village'],'Total':r['total'],'Done':r['done']} for r in top])).mark_bar(
                color=PALETTE['orange'],cornerRadiusEnd=5).encode(
                x=alt.X('Total:Q',title='Listed locations'),
                y=alt.Y('Village:N',sort='-x',title=None,axis=alt.Axis(labelLimit=200)),
                tooltip=['Village','Total','Done']).properties(height=max(210,len(top)*29))
            st.altair_chart(graph,use_container_width=True)
            st.dataframe([{'Village / ग्राम':v['village'],'Total / कुल':v['total'],'Done':v['done'],
                           'Not marked Done / शेष':v['unmarked'],'Done %':v['percent']} for v in village_summary],
                         hide_index=True,use_container_width=True)
    else:
        st.info(tr('nodata'))
    st.caption('All-time total across the shared sheet: '+str(solar_summary(rows)['total'])+' listed locations.' if lang=='English'
               else 'साझा शीट में कुल '+str(solar_summary(rows)['total'])+' स्थल दर्ज हैं।')
    st.markdown('<div class="solar-note">'+esc(
        'The sheet has no date or coordinator columns. “Done” means marked Done in the source, not independently verified installation.'
        if lang=='English' else
        'इस शीट में तारीख या संयोजक कॉलम नहीं है। “Done” का अर्थ मूल शीट में दर्ज स्थिति है, स्वतंत्र स्थापना सत्यापन नहीं।')+'</div>',
        unsafe_allow_html=True)


def set_page(page):
    st.session_state['page_v5']=page


def set_report(kind):
    """Callback updates report context before any widgets are rendered.
    Deliberately leaves coordinator, period and location filters untouched.
    """
    if kind not in TABS and kind != "solar":
        return
    st.session_state['report_v5']=kind
    st.session_state['saved_report_v52']=kind
    st.session_state['page_v5']='reports'


def main_navigation():
    """Four large buttons remain accessible even when the sidebar is hidden on phones."""
    labels={
        'home':'⌂ '+tr('home'),
        'reports':'▦ '+tr('reports'),
        'dates':'▤ '+tr('dates'),
        'team':'♙ '+tr('team'),
    }
    st.markdown('<div class="sa-nav-label">'+esc(
        'Navigate / मुख्य मेन्यू' if lang=='English' else 'मुख्य मेन्यू / Navigate'
    )+'</div>',unsafe_allow_html=True)
    for pair in (('home','reports'),('dates','team')):
        cols=st.columns(2,gap='small')
        for column,destination in zip(cols,pair):
            with column:
                st.button(labels[destination], key=f'main_nav_btn_{destination}',
                          on_click=set_page, args=(destination,),
                          type='primary' if st.session_state.get('page_v5')==destination else 'secondary',
                          use_container_width=True)
    if st.session_state.get('page_v5')=='health':
        st.button('← '+tr('home'),on_click=set_page,args=('home',),
                  key='health_return_home',use_container_width=True)


def report_navigation():
    """Two-column button grid: six reporting sections, no dropdown to reopen."""
    icons={
        'daily':'📅','registration':'👥','whatsapp':'💬',
        'actions':'📝','booth':'🗳️','social':'📱','solar':'☀️',
    }
    keys=list(TABS)+["solar"]
    st.markdown('<div class="sa-nav-label">'+esc(
        'Choose a reporting section / रिपोर्ट चुनें'
    )+'</div>',unsafe_allow_html=True)
    for start in range(0,len(keys),2):
        pair=keys[start:start+2]
        cols=st.columns(1 if len(pair)==1 else 2,gap='small')
        for column,key in zip(cols,pair):
            with column:
                report_label=SOLAR_LABEL[lang] if key=='solar' else TABS[key]['hi' if lang=='हिंदी' else 'en']
                st.button(f'{icons[key]} {report_label}', 
                          key=f'report_btn_{key}',on_click=set_report,args=(key,),
                          type='primary' if st.session_state.get('report_v5')==key else 'secondary',
                          use_container_width=True)
    return st.session_state['report_v5']


# The MP's selection is one office-wide context. Values survive switching report types/pages.
def _persist_scope():
    st.session_state['scope_worker_saved']=st.session_state['scope_worker_widget']


def _persist_period():
    st.session_state['scope_period_saved']=st.session_state['scope_period_widget']


def reset_filters(kind=None):
    st.session_state['scope_worker_saved']=ALL
    st.session_state['scope_worker_widget']=ALL
    st.session_state['scope_period_saved']='all'
    st.session_state['scope_period_widget']='all'
    st.session_state['scope_include_undated']=False
    st.session_state.pop('scope_custom_dates',None)
    if kind:
        for suffix in ('booth','village','search'):
            st.session_state.pop(f'extra_{kind}_{suffix}',None)


def date_choice(key,kind=None):
    opts=['all','today','yesterday','week','month','custom']
    if 'scope_period_saved' not in st.session_state: st.session_state.scope_period_saved='all'
    if 'scope_period_widget' not in st.session_state:
        st.session_state.scope_period_widget=st.session_state.scope_period_saved
    period=st.selectbox(('SP joining-date period / सपा से जुड़ने की अवधि' if kind=='registration' else 'Period / अवधि'),
                        opts,format_func=tr,key='scope_period_widget',on_change=_persist_period)
    today=NOW.date();low=high=None
    if period=='today':low=high=today
    elif period=='yesterday':low=high=today-dt.timedelta(days=1)
    elif period=='week':low=today-dt.timedelta(days=6);high=today
    elif period=='month':low=today-dt.timedelta(days=29);high=today
    elif period=='custom':
        dates=st.date_input('From / To · से / तक',value=(today-dt.timedelta(days=7),today),key='scope_custom_dates')
        if isinstance(dates,(list,tuple)) and len(dates)==2:low,high=dates
        else:st.info('Select a start and end date / शुरू और अंतिम तारीख चुनें')
    include=False
    if period!='all':include=st.checkbox(tr('undated'),key='scope_include_undated',value=False)
    return low,high,include


def filters(key,kind=None):
    if 'scope_worker_saved' not in st.session_state: st.session_state.scope_worker_saved=ALL
    if 'scope_worker_widget' not in st.session_state:
        st.session_state.scope_worker_widget=st.session_state.scope_worker_saved
    c1,c2=st.columns(2,gap='small')
    with c1:
        person=st.selectbox('Coordinator / संयोजक',[ALL]+[p['en'] for p in COORDINATORS],
                            format_func=person_name,key='scope_worker_widget',on_change=_persist_scope)
    with c2:low,high,include=date_choice(key,kind)
    st.markdown('<div class="scope-hint">'+esc(
        'This coordinator and date selection stays active when you switch reports.'
        if lang=='English' else 'संयोजक और तारीख का चयन अन्य रिपोर्ट खोलने पर भी बना रहेगा।')+'</div>',
        unsafe_allow_html=True)
    booth='All booths'; village=tr('village_all');query=''
    if kind:
        base=[r for r in data[kind] if person==ALL or r.get('_coordinator')==person]
        with st.expander('🔎 '+tr('filter'),expanded=False):
            opts=sorted({normalized_booth(r.get('booth')) for r in base if normalized_booth(r.get('booth'))})
            booth=st.selectbox(tr('booth'),['All booths']+opts,key=f'extra_{kind}_booth')
            villages=sorted({str(r.get('panchayat','')).strip() for r in base if str(r.get('panchayat','')).strip()})
            village=st.selectbox(tr('village'),[tr('village_all')]+villages,key=f'extra_{kind}_village')
            query=st.text_input(tr('search'),key=f'extra_{kind}_search',
                                placeholder='Name, village, issue… / नाम, गांव, समस्या…')
    st.button('↺ '+tr('reset'),key=f'reset_filters_{key}',on_click=reset_filters,args=(kind,),
              help='Clear coordinator, period and extra filters' if lang=='English' else 'सभी फ़िल्टर हटाएँ')
    return person,low,high,include,booth,query,village


def apply_extra_location(records,village):
    if village in (None,'',LABEL['English']['village_all'],LABEL['हिंदी']['village_all']):
        return records
    return [r for r in records if str(r.get('panchayat','')).strip()==str(village).strip()]

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
if 'saved_report_v52' not in st.session_state:st.session_state.saved_report_v52='daily'
if 'report_v5' not in st.session_state:st.session_state.report_v5=st.session_state.saved_report_v52
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
    if 'source_v5' not in st.session_state:st.session_state['source_v5']='Live Google Sheets'
    with st.expander('📂 Original Google Sheets / मूल गूगल शीट', expanded=False):
        st.caption('Choose a coordinator to open the original sheet in a new tab. / संयोजक की मूल शीट खोलें।')
        for member in COORDINATORS:
            # Stable IDs are bundled in config.py; no editable external URLs are accepted.
            st.markdown(
                f'<a href="https://docs.google.com/spreadsheets/d/{esc(member["id"])}/edit" '
                f'target="_blank" rel="noopener noreferrer">📄 {esc(member["en"])}</a>',
                unsafe_allow_html=True,
            )
    with st.expander('☀ Solar Light verification / सोलर लाइट शीट', expanded=False):
        st.markdown(f'<a href="{esc(SOLAR_SHEET_URL)}" target="_blank" rel="noopener noreferrer">'
                    '📄 Solar Light verification Manjhanpur</a>',unsafe_allow_html=True)
    if st.button('🔄 '+tr('refresh'),use_container_width=True,key='reload_side_v5'):
        st.cache_data.clear();st.rerun()
    with st.expander('⚙ Office settings / कार्यालय सेटिंग'):
        source=st.selectbox('Data source / डेटा स्रोत', ['Live Google Sheets','Sample (fictional)','Upload XLSX (offline)'],key='source_v5')
        if st.button('View connection status',key='goto_health_v5',use_container_width=True,on_click=set_page,args=('health',)):
            pass
        st.caption('9 original sheets · 54 report tabs')
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

# The shared Solar Light source is independent from the 9 × 6 coordinator feeds.
solar_rows=[];solar_connected=False;solar_error=None
if source=='Live Google Sheets' and account and password:
    @st.cache_data(ttl=48,show_spinner='Checking shared Solar Light verification sheet…')
    def solar_online(_account): return load_solar_online(_account)
    try:
        solar_rows=solar_online(account)
        solar_connected=True
    except Exception as exc:
        solar_error=f'{type(exc).__name__}: {exc}'
connected=sum(1 for entry in health if entry.get('ok'))
total=len(COORDINATORS)*len(TABS)

brand_header()
# Keep language easily accessible without requiring a sidebar on mobile.
lang_col1,lang_col2=st.columns([2.3,1],gap='small')
with lang_col1:
    st.caption('Saarthi Analytics · Field reports / फील्ड रिपोर्ट')
with lang_col2:
    lang=st.selectbox('Language / भाषा',['English','हिंदी'],key='language_v5')
main_navigation()
page=st.session_state['page_v5']
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
    st.markdown(f'<span class="scope-chip">{esc(tr("active"))}: {esc(person_name(who))}</span>',unsafe_allow_html=True)
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
        # Shared-team verification is not attributed to the 9 individual coordinators.
        if solar_connected:
            solar_stats=solar_summary(solar_rows)
            heading('☀ '+SOLAR_LABEL[lang])
            metric_cards([('Solar sites / सोलर स्थल',solar_stats['total']),
                          ('Marked Done / पूर्ण',solar_stats['done']),
                          ('Not marked Done / शेष',solar_stats['unmarked'])])
            st.button('☀ '+('Open Solar Light Verification' if lang=='English' else 'सोलर सत्यापन खोलें'),
                      on_click=set_report,args=('solar',),key='solar_home_btn',use_container_width=True)
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
            for r in (row for tab in TABS if tab!='registration' for row in picked[tab]):
                if r.get('_date'):
                    date=r['_date'].isoformat();daily[date]=daily.get(date,0)+1
            if not make_chart([{'Date':d,'Value':v} for d,v in sorted(daily.items())],'Date','Value',mode='line',height=305):
                st.info(tr('nodates'))
            st.caption('Youth worker joining dates are excluded from daily field reporting.' if lang=='English' else 'युवा कार्यकर्ताओं के पार्टी से जुड़ने की तारीख को दैनिक फील्ड रिपोर्टिंग में नहीं जोड़ा गया है।')
        heading(tr('quick'))
        c1,c2,c3=st.columns(3,gap='small')
        with c1:st.button('▣ '+tr('reports'),on_click=set_page,args=('reports',),use_container_width=True,type='primary',key='go_reports_v5')
        with c2:st.button('▤ '+tr('dates'),on_click=set_page,args=('dates',),use_container_width=True,key='go_dates_v5')
        with c3:st.button('♙ '+tr('team'),on_click=set_page,args=('team',),use_container_width=True,key='go_team_v5')
    else:
        st.warning('Connection is not ready. Open Connection Status from Office tools. No figures are fabricated.' if lang=='English' else 'कनेक्शन चालू नहीं है। कार्यालय सेटिंग से कनेक्शन जांचें।')
        if failure:st.caption(failure)

elif page=='reports':
    kind=report_navigation()
    if kind=='solar':
        solar_report(solar_rows,solar_connected,solar_error)
    else:
        hero(tr('reports'),'Select one report, apply filters, then view charts and records.' if lang=='English' else 'रिपोर्ट चुनें, फिल्टर लगाएँ और ग्राफ तथा रिकॉर्ड देखें।')
        st.markdown('<div class="sa-selected-report">'+esc(TABS[kind]['hi' if lang=='हिंदी' else 'en'])+'</div>',unsafe_allow_html=True)
        st.caption('Your coordinator selection will stay the same when you change reports.' if lang=='English' else 'रिपोर्ट बदलने पर आपका चुना हुआ संयोजक नहीं बदलेगा।')
        if kind == 'registration':
            st.info(REG_DATE_NOTE[lang])
        who,low,high,include,booth,query,village=filters('reports_'+kind,kind)
        st.markdown(f'<span class="scope-chip">{esc(tr("active"))}: {esc(person_name(who))}</span>',unsafe_allow_html=True)
        if loaded:
            records=apply_extra_location(filter_rows(data[kind],who,low,high,include,query=query,booth=booth),village)
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
                    heading(REG_TREND_LABEL[lang] if kind=='registration' else tr('bydate'))
                    if not make_chart(trend(records,kind),'Date','Value',mode='line',height=285):st.info(tr('nodates'))
                    if kind=='registration':
                        st.caption(REG_DATE_NOTE[lang])
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
    hero(tr('dates'),('Daily field reporting and party joining dates are shown separately.'
                      if lang=='English' else 'दैनिक रिपोर्ट और पार्टी से जुड़ने की तारीख अलग-अलग दिखाई गई हैं।'))
    who,low,high,include,*_=filters('date_report')
    if loaded:
        matrix=daily_matrix(data,who,low,high,include,filter_rows)
        scoped={k:filter_rows(data[k],who,low,high,include) for k in TABS}
        metric_cards([(TABS[k]['hi' if lang=='हिंदी' else 'en'],stats(v)['additions'] if k=='whatsapp' else len(v)) for k,v in scoped.items()])
        byday=[{'Date':r['Date'],'Value':sum(r[k] for k in TABS if k not in ('whatsapp','registration'))} for r in matrix]
        wa=[{'Date':r['Date'],'Value':r['whatsapp']} for r in matrix]
        c1,c2=st.columns(2,gap='medium')
        with c1:
            heading('Report entries / रिपोर्ट एंट्री')
            if not make_chart(byday,'Date','Value',mode='line'):st.info(tr('nodates'))
        with c2:
            heading(tr('wa'))
            if not make_chart(wa,'Date','Value'):st.info(tr('nodates'))
        heading(REG_TREND_LABEL[lang])
        registration_joining=[{'Date':r['Date'],'Value':r['registration']} for r in matrix if r['registration']]
        if not make_chart(registration_joining,'Date','Value',mode='line',height=240):
            st.info('No recorded joining dates for this selection.' if lang=='English' else 'इस चयन में जुड़ने की तारीख नहीं मिली।')
        st.caption(REG_DATE_NOTE[lang])
        heading(tr('table'))
        if matrix:
            table=[{'Date / दिनांक':r['Date'],**{(('Youth joined SP (count)' if lang=='English' else 'सपा से जुड़े युवा (संख्या)') if k=='registration' else TABS[k]['hi' if lang=='हिंदी' else 'en']):r[k] for k in TABS}} for r in matrix]
            st.dataframe(table,hide_index=True,use_container_width=True)
            st.download_button('⬇ '+tr('download'),csv_file(table),file_name='saarthi_daily_summary.csv',mime='text/csv',key='daily_export_v5')
        else:st.info(tr('nodates'))
        undated={kind:sum(r.get('_date') is None for r in recs) for kind,recs in scoped.items()}
        if any(undated.values()):
            with st.expander(tr('unknown')):
                st.dataframe([{'Report':TABS[k]['hi' if lang=='हिंदी' else 'en'],'Undated records':v} for k,v in undated.items() if v],hide_index=True)
                st.caption('Missing dates are excluded from date charts. In Youth Worker Registration, the missing date refers to when a person joined the Samajwadi Party, not data entry.' if lang=='English' else 'बिना तारीख वाले रिकॉर्ड दिनांकवार ग्राफ में नहीं आते। युवा कार्यकर्ता पंजीकरण में तारीख पार्टी से जुड़ने की है, डेटा भरने की नहीं।')
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
                  'Daily entries / दैनिक एंट्री':len(d),'Youth registrations / युवा पंजीकरण':len(reg),
                  'WA additions / नए सदस्य':stats(wa)['additions'],
                  'Unique groups / अलग ग्रुप':stats(wa)['groups'],
                  'Action records / कार्रवाई':len(act)})
        metric_cards([('Coordinators / संयोजक',len(workers)),('Report entries / एंट्री',sum(len(x) for x in scoped.values())),(tr('wa'),stats(scoped['whatsapp'])['additions'])])
        heading(tr('byworker'))
        chart=[{'Coordinator':r['Coordinator / संयोजक'],'Value':r['Daily entries / दैनिक एंट्री']+r['Youth registrations / युवा पंजीकरण']+r['Action records / कार्रवाई']} for r in team_records]
        if not make_chart(chart,'Coordinator','Value',horizontal=True,height=325):st.info(tr('nodata'))
        st.caption('Comparison excludes WhatsApp addition counts because people-addition totals are different units from report entries.')
        heading(tr('table'))
        st.dataframe(team_records,hide_index=True,use_container_width=True)
        st.download_button('⬇ '+tr('download'),csv_file(team_records),file_name='saarthi_coordinator_summary.csv',mime='text/csv',key='team_export_v5')
    else:st.info(tr('nodata'))

elif page=='health':
    hero(tr('health'),'Office-only diagnostic view · Nine coordinator sheets × six reporting sections + one shared Solar sheet')
    metric_cards([('Readable tabs',connected if loaded else '—'),('Expected tabs',total),('Google Sheets',len(COORDINATORS)),('Undated records',sum(r.get('undated',0) for r in health))])
    heading('☀ '+SOLAR_LABEL[lang])
    if source!='Live Google Sheets':
        st.caption('Solar Light is a LIVE-only source; offline coordinator snapshots do not include it.')
    elif solar_connected:
        ss=solar_summary(solar_rows)
        st.success(f'Connected · {ss["total"]} listed locations · {ss["done"]} marked Done')
    else:
        st.warning('Shared Solar Light source not connected. Grant the same service account Viewer access to the Solar Light Google Sheet.')
        if solar_error:st.caption(str(solar_error)[:240])
    st.link_button('Open shared Solar Light sheet',SOLAR_SHEET_URL)
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
