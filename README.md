# Manjhanpur 252 · Live Field Operations Dashboard V3

This is a **Streamlit dashboard for nine original, private Google Sheets**. It reads them directly using the Google Sheets API, merges the six standard reporting sections from each coordinator, and refreshes around every 60 seconds. **It never modifies any original sheet.**

## Fixes in V3

- The **Command Center is the default first page**, with public-reference portraits of MP Pushpendra Saroj and MLA Indrajeet Saroj; it never disappears behind an upload request.
- Photos appear before overview statistics, coordinator comparison, and six report-navigation cards.
- **LIVE** is the default source. If private Google permissions are missing, the homepage still displays and the metrics read `—` with a clear connection checklist. This is intentionally not shown as zero or live data.
- All six reporting tabs include coordinator, booth, date range, undated-inclusion and keyword filters. The Date-wise Report gives section-wise and dated activity summaries. English/Hindi UI switch is available.
- **No duplicate group count**: multiple additions to the same WhatsApp group are summed as additions; the group is counted once by its normalized link/name. We cannot guarantee unique individuals from counts alone.
- Quality monitoring shows all 54 source-tab statuses. The source's blank numbered rows do not count.
- **Sample preview** is available *only when explicitly selected*, and is clearly labeled as fictional and **not live**. XLSX upload is optional and also not live.
- The application does **not** automatically machine-translate arbitrary personal ground notes; UI headings and known categories are translated, while free text stays in its original language.

## Run in VS Code (Windows)

Open this extracted folder, **the folder containing app.py**, in VS Code. Terminal → New Terminal:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8503
```

Open **http://localhost:8503**. The homepage will now be visible immediately.

If you **already installed packages for V2** and want to avoid reinstalling, copy all V3 files over the V2 folder (keeping your existing `.venv`) or use that existing environment's Python executable to run the V3 `app.py`.

## Critical: enable actual LIVE Google Sheets access

**This setup is needed once, not every day.** Merely knowing private Google Sheet URLs isn't permission to read them from Streamlit. The Google Drive account linked in ChatGPT does not authorize a local VS Code process.

1. Go to [Google Cloud Console](https://console.cloud.google.com/). Create/select a project, enable **Google Sheets API**.
2. IAM & Admin → **Service Accounts** → Create service account. Make it dedicated to read-only access; no special Google Cloud project role is necessary for viewing Sheets shared directly with this account.
3. Under this service account, create a **JSON key** if your Google organization permits keys. Keep it confidential.
4. Copy `client_email` from the JSON. Open each of the **nine original Google Sheets**. Click **Share** → enter that email → grant **Viewer**. Do this in all nine. Never set original field sheets to public.
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (same directory). Copy fields from JSON under `[gcp_service_account]`. Replace the `dashboard_password` placeholder with a strong office password. In `private_key`, preserve the `\n` escaped line breaks, as shown in the example.
6. Restart Streamlit. Enter the office password. Sidebar should say **Private connection configured**, and top status should report **LIVE — 54/54 tabs connected**. Check Connection & Quality if it doesn't.
7. In any source Sheet (e.g., Vivek's WhatsApp tab), change an addition count; Save (Google does so automatically). Back in dashboard click **↻ Refresh data**. The totals and source row should reflect your edit. No other source Sheet needs to be open.

**Security:** `.streamlit/secrets.toml` and any key JSON are excluded by `.gitignore`. Don't paste them into chat, email or WhatsApp and don't publish the dashboard publicly for real field data. The MVP office password is a lightweight gate; use identity-based access control in production.

## Data accuracy

The WhatsApp Group tab in most original files has **no `Entry Date` column**. Its all-time additions and unique groups remain visible. To report additions *on a particular day*, the field coordinators must add an explicitly labeled `Entry Date`/`दिनांक` column to the corresponding tab, then record the date of **each new row**. The app finds this extra column without changing existing positions. Dates are never guessed. Adding a date column similarly improves Actionable Points, Booth Worker Status and Social Media date filters.

Some original data is in Hindi; UI labels and common category values are translated to English when English is selected, but arbitrary paragraphs are not translated to avoid sending confidential field text to an external translation service.

## Source links

The nine current original Sheet IDs are defined in `config.py`; coordinator names match the original nine list. The data source is **not** the previous three fictional Sheets.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
