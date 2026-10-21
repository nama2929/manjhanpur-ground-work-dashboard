"""Shared-team solar light verification reader (read-only).

Not part of the nine coordinator workbooks. The source has no verification date
or coordinator field; do not manufacture them. Never expose full phone numbers.
"""
from __future__ import annotations
from collections import defaultdict
import re

SOLAR_SHEET_ID = '1gJC86hrLtqke-y78xR-moVNB_KF89H8BH5k5BP6KaHg'
SOLAR_TAB = 'Sheet1'
SOLAR_SHEET_URL = 'https://docs.google.com/spreadsheets/d/' + SOLAR_SHEET_ID + '/edit'


def _cell(row, i):
    return str(row[i] if len(row) > i and row[i] is not None else '').strip()


def normalize_solar_rows(rows):
    """Accept A3:G values, beginning with the real Hindi column header."""
    if not rows:
        return []
    header = [str(v).strip() for v in rows[0]]
    # Fail instead of treating an unrelated tab as the verification dataset.
    if len(header) < 7 or 'ग्राम' not in header[1] or 'स्थल' not in header[2]:
        raise ValueError('Unexpected Solar Light sheet columns. Expected A:G: serial, village, site, name, father, mobile, Done.')
    result = []
    for n,row in enumerate(rows[1:], 4):
        serial=_cell(row,0)
        village=_cell(row,1)
        site=_cell(row,2)
        contact=_cell(row,3)
        father=_cell(row,4)
        phone=_cell(row,5)
        raw_status=_cell(row,6)
        if not any((serial,village,site,contact,father,phone,raw_status)):
            continue
        # A populated serial alone is not a verified site; preserve as a listed
        # location if at least the site/village exists.
        if not village and not site:
            continue
        done=raw_status.casefold().strip() in {'done', 'completed', 'verified', 'yes', 'हाँ', 'हो गया', '✓', '✔'}
        result.append({'serial':serial or str(n-3), 'village':village,'site':site,
                       'contact':contact,'father':father,'phone':phone,
                       'status_raw':raw_status, 'done':done,'row':n})
    return result


def load_solar_online(service_account):
    """Read only A3:G800 from the independent, team-shared spreadsheet."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds=Credentials.from_service_account_info(dict(service_account),scopes=scopes)
    client=gspread.authorize(creds)
    sheet=client.open_by_key(SOLAR_SHEET_ID).worksheet(SOLAR_TAB)
    data=sheet.get('A3:G800',value_render_option='FORMATTED_VALUE')
    return normalize_solar_rows(data)


def solar_summary(rows):
    total=len(rows)
    completed=sum(bool(r['done']) for r in rows)
    return {'total':total,'done':completed,'unmarked':total-completed,
            'pct':round(100*completed/total,1) if total else 0.0,
            'villages':len({r['village'].strip() for r in rows if r['village'].strip()})}


def solar_villages(rows):
    grouped=defaultdict(lambda: {'total':0,'done':0})
    for row in rows:
        village=row['village'].strip() or '(Unnamed village)'
        grouped[village]['total']+=1
        grouped[village]['done']+=int(bool(row['done']))
    output=[]
    for village, counts in grouped.items():
        total=counts['total'];done=counts['done']
        output.append({'village':village,'total':total,'done':done,'unmarked':total-done,
                       'percent':round(100*done/total,1) if total else 0})
    return sorted(output,key=lambda r:(-r['total'],r['village']))


def solar_filter(rows,village='All villages',status='All',query=''):
    q=str(query or '').strip().casefold()
    chosen=[]
    for row in rows:
        if village!='All villages' and row['village']!=village:
            continue
        if status=='Done' and not row['done']:
            continue
        if status=='Not marked Done' and row['done']:
            continue
        if q and not any(q in str(row[k]).casefold() for k in ('serial','village','site','contact','father')):
            continue
        chosen.append(row)
    return chosen


def masked_phone(value):
    digits=re.sub(r'\D','',str(value or ''))
    if not digits:return ''
    return '••••••'+digits[-4:] if len(digits)>=4 else '••••'
