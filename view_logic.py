"""Pure reporting summaries for the mobile-first dashboard.
No source-sheet writes, guessed dates, or estimated people counts.
"""
from collections import Counter, defaultdict
from data_layer import normalized_booth, stats, to_int, display_value
from config import COORDINATORS, TABS


def trend(rows, kind):
    by_day = defaultdict(int)
    for row in rows:
        date = row.get('_date')
        if date is not None:
            by_day[date.isoformat()] += (to_int(row.get('additions')) if kind == 'whatsapp' else 1)
    return [{'Date': day, 'Value': by_day[day]} for day in sorted(by_day)]


def coordinator_activity(rows, kind, lang='English', include_zeros=False):
    values = defaultdict(int)
    for row in rows:
        values[row.get('_coordinator', '')] += to_int(row.get('additions')) if kind == 'whatsapp' else 1
    entries = []
    for worker in COORDINATORS:
        count = values[worker['en']]
        if count or include_zeros:
            entries.append({'Coordinator': worker['hi'] if lang == 'हिंदी' else worker['en'],
                            'Value': count})
    return sorted(entries, key=lambda x: (-x['Value'], x['Coordinator']))


def category_counts(rows, field, lang='English', cap=12):
    count = Counter()
    for row in rows:
        raw = str(row.get(field, '') or '').strip()
        if raw:
            count[display_value(field, raw, lang)] += 1
    return [{'Category': name, 'Value': qty} for name,qty in count.most_common(cap)]


def group_summary(rows, lang='English'):
    """One summary per distinct WhatsApp group; additions are summed across entries."""
    grouped = {}
    for row in rows:
        key = row.get('_group_key')
        if not key:
            continue
        if key not in grouped:
            grouped[key] = {'Group': row.get('group', '') or '(unnamed)', 'New additions': 0,
                            'Entries': 0, 'Coordinators': set()}
        g = grouped[key]
        g['New additions'] += to_int(row.get('additions', 0))
        g['Entries'] += 1
        g['Coordinators'].add(row.get('_coordinator', ''))
    output = []
    for group in grouped.values():
        output.append({'Group': group['Group'], 'New additions': group['New additions'],
                       'Entries': group['Entries'], 'Coordinators': len(group['Coordinators'])})
    return sorted(output, key=lambda x: (-x['New additions'], str(x['Group'])))


def summarize_section(rows, kind):
    booths = {normalized_booth(r.get('booth')) for r in rows if normalized_booth(r.get('booth'))}
    count = stats(rows)
    return {'records': len(rows), 'booths': len(booths), 'undated': count['undated'],
            'groups': count['groups'], 'additions': count['additions'],
            'coordinators': len({r.get('_coordinator') for r in rows})}


def daily_matrix(data, worker, low, high, include_undated, filter_fn):
    """Real date only: undated rows are not assigned to a day."""
    bydate = {}
    for kind in TABS:
        records = filter_fn(data[kind], worker, low, high, include_undated)
        for r in records:
            day = r.get('_date')
            if day is None:
                continue
            k = day.isoformat()
            if k not in bydate:
                bydate[k] = {'Date': k, **{t: 0 for t in TABS}}
            bydate[k][kind] += to_int(r.get('additions')) if kind == 'whatsapp' else 1
    return [bydate[k] for k in sorted(bydate)]
