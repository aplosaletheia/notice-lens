# NoticeLens

> Automatically monitor college notice boards, process new notices, and extract information relevant to you.

## 🚧 Project Status

NoticeLens is an ongoing hackathon project.

The current implementation focuses on:
- Fetching a college notices webpage
- Parsing the webpage for notice links
- Identifying new notices
- Retrieving documents from notice links
- Processing retrieved documents with an LLM
- Filtering information based on the student's profile

More functionality will be added as development progresses.

---

## 💡 The Problem

College students receive important information through notices published on their college websites.

These notices can contain:

- Assignment deadlines
- Examination dates
- Registration deadlines
- Internship opportunities
- Scholarship announcements
- Competition/hackathon information
- Important events
- Administrative instructions
- Changes to schedules

The problem is that students are generally expected to **manually check the college notice webpage**, open individual notices, read through the documents, and determine whether anything is relevant to them.

This becomes especially inconvenient when:

1. The notice page contains many documents.
2. New notices are added frequently.
3. Notices are stored as PDFs or scanned documents.
4. Important information is buried inside a long document.
5. Different notices are relevant to different students.

### Example

A college notice board might contain:

```text
Notice 1 → B.Tech examination schedule
Notice 2 → Faculty recruitment
Notice 3 → Scholarship information
Notice 4 → Internship opportunity
Notice 5 → M.Tech admission
Notice 6 → B.Tech 3rd semester examination
...
