# noticeLens

> A personal assistant that reads your college's notice board so you don't have to.

**Hackathon:** WCC Launchpad 30 (4-5 Oct 2026) | **Track:** Everyday Automation
**Team:** `arpit` | `Arpit Sharma`
**Demo video:** `[<LINK>](https://www.youtube.com/@AplosAletheia)` | **Repository:** `[<LINK>](https://github.com/aplosaletheia/notice-lens.git)`

---

## The problem

College notice boards are a firehose. Notices are posted as PDFs (sometimes scanned photos of paper), buried in long lists, with no filtering. Students either check obsessively or miss registration deadlines for hackathons, contests, scholarships and events they would have wanted.

Notices are issued per institute, but relevance is personal: your year, your branch, your interests, and whether an event hosted elsewhere is open to you.

## What it does

noticeLens checks a notices page, finds only the **new** notices, downloads each document, and uses an LLM to decide whether it matters to **you**. Relevant notices become structured, scannable data. Irrelevant ones are dropped.

1. **Scrape** the notices page and extract notice links.
2. **Track** the last processed notice, so only new ones are handled on later runs.
3. **Retrieve** each document: plain HTTP first, browser automation (Playwright) as a fallback for redirects, new tabs and session-bound links.
4. **Read** the PDF text (the LLM also handles scanned documents).
5. **Judge** relevance (0-1) against your student profile, and extract dates, times, registration windows, location, category and a short summary.
6. **Store** only relevant results, plus a copy of the PDF.

### Example output

```json
{
  "relevance": 0.7,
  "name": "event_name.pdf",
  "event": {
    "name": "",
    "location": "",
    "registration": { "start_date": "", "start_time": "", "end_date": "", "end_time": "" },
    "event_start": { "date": "", "time": "" },
    "event_end": { "date": "", "time": "" },
    "category": "",
    "sub_category": ""
  },
  "summary": { "objective": "", "important_people": [], "scope": "" }
}
```

## Why it fits "Everyday Automation"

It takes a repetitive, unglamorous job (scanning notices) off the student's day and runs without supervision:

- **Time given back:** read a few relevant summaries instead of dozens of PDFs.
- **Mistakes stopped:** missed registration deadlines.
- **No re-work:** a notice gate guarantees old notices are never reprocessed.

## Design highlights

| Area | What we did |
|---|---|
| **Reliable retrieval** | HTTP first, then a real browser that clicks the link like a user would and judges only what the browser actually displays (`document.contentType`). Handles redirects, new tabs and session-bound URLs. |
| **Scope-aware relevance** | The prompt tells the model not to treat "issued by my institute" as "relevant to me", and to allow large open events hosted elsewhere. Scores under 0.5 are treated as 0. |
| **Scanned documents** | Handled through the LLM step. |
| **Validated output** | LLM output must be valid JSON with a numeric relevance, or it is rejected and never stored. |
| **Failures never block** | Per-document error handling; failed notices are reported with a reason instead of crashing the run. |
| **Site-agnostic core** | Site-specific logic is separated from the pipeline. Tested on the NSUT (`imsnsit.org`) and IITD (`academics.iitd.ac.in/circulars`) notice pages. |
| **User control** | The relevance prompt, profile and state are all user-editable from the CLI. |

## Dependencies

Requires **Python 3.10+**.

| Package | Used for |
|---|---|
| `requests` | HTTP document retrieval |
| `pypdf` | Extracting text from PDFs |
| `playwright` | Browser automation fallback (redirects, new tabs, session-bound links) |
| `beautifulsoup4` | Parsing the notices page HTML |
| `google-genai` | LLM calls (Google Gemini API) |

Everything else (`sys`, `json`, `re`, `pathlib`, `io`, `urllib`, `os`, `pickle`, `copy`) is part of the Python standard library.

## Setup

```bash
git clone <REPO_URL>
cd <REPO_DIR>

pip install -r requirements.txt
playwright install chromium

cd ".\.src\"

python main.py api-key set <YOUR_API_KEY>
python main.py profile edit
python main.py notices set "https://academics.iitd.ac.in/circulars/"

python main.py            # check for new notices
```

`requirements.txt`:

```
requests
pypdf
playwright
beautifulsoup4
google-genai
```

## CLI reference

```
python main.py                       Check for new notices
python main.py notices [check|show|set <url>]
python main.py profile [show|edit|set <field> <value>]
python main.py prompt  [show|set]    (end input with a line containing END-)
python main.py api-key [show|set <key>|clear]
python main.py last-url [show|set <url>|clear]
python main.py final   [show|clear]  View / clear stored relevant results
python main.py state   [show|clear]
python main.py help
```

Profile fields: `name, institute, course, branch, year, semester, section, roll_number, interests, notices_url`.

## Demo flow (about 2 minutes)

1. `python main.py profile show` shows the student profile.
2. `python main.py notices set "<url>"` points at a notices page.
3. `python main.py` runs the pipeline: scrape, gate, retrieve, LLM.
4. A relevant notice is stored and its PDF saved.
5. An irrelevant notice is rejected.
6. `python main.py final show` shows the structured results.
7. Re-run `python main.py` to show nothing is reprocessed.

## Responsible design and trust

- **Humans stay in control:** the tool only filters and summarises. It never registers or acts on the student's behalf.
- **Transparent:** relevance scores are printed for every document, and the prompt is visible and editable.
- **Local storage:** the profile and results are stored locally.
- **Known risk:** the API key is stored in the local state file (`notice_state.bin`) without encryption. Do not commit that file.
- **Known risk:** a model can misjudge relevance, so low-relevance notices may deserve a spot check. Nothing is deleted from the source site.

## Known limitations

- Only PDF notices are supported (no DOCX, image-only or HTML-only notices yet).
- Notice-page parsing is tuned for the pages tested; unusual layouts may need parser changes.
- If the last processed notice disappears from the homepage, the run is skipped to avoid reprocessing old documents.
- Failed documents are not retried automatically.
- Relevance quality depends on the profile and prompt provided.

## Disclosure

- **AI tools used:** `<LIST, e.g. Claude for code assistance, Gemini API for notice analysis>`
- **Libraries:** see Dependencies above.
- **Pre-existing work:** `<If any code or ideas predate 4 Oct 2026, state exactly what, per the event rules.>`

## Built for

[WCC Launchpad 30]