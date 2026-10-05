# Developer Roadmap

## Phase 1 — Notice Webpage

- [x] Fetch webpage HTML
- [x] Parse HTML
- [ ] Identify notice links
- [ ] Extract notice metadata
- [ ] Test against the NSUT notices page

## Phase 2 — Notice Tracking

- [ ] Detect newly added notices
- [ ] Store identifiers for processed notices
- [ ] Prevent unnecessary reprocessing
- [ ] Test first-run vs subsequent-run behavior

## Phase 3 — Document Retrieval

- [ ] Support direct document URLs
- [ ] Support redirecting links
- [ ] Add browser automation
- [ ] Handle documents opened in new tabs
- [ ] Capture downloaded documents
- [ ] Handle retrieval failures
- [ ] Delete temporary documents after processing

## Phase 4 — AI Processing

- [ ] Choose LLM/API
- [ ] Define structured output format
- [ ] Send documents to the LLM
- [ ] Extract dates and times
- [ ] Extract relevant notice information
- [ ] Determine notice relevance to the student
- [ ] Handle scanned documents/images
- [ ] Handle ambiguous or incomplete information
- [ ] Validate structured LLM output

## Phase 5 — Student Profile

- [ ] Define student profile fields
- [ ] Create profile input/storage
- [ ] Use profile information for relevance filtering
- [ ] Test relevant vs irrelevant notices

## Phase 6 — User Interface

- [ ] Design initial UI
- [ ] Display processed notices
- [ ] Display extracted dates/events
- [ ] Display source/evidence where appropriate
- [ ] Allow users to review extracted information
- [ ] Handle errors clearly

## Phase 7 — Google Calendar Integration

- [ ] Set up Google Cloud project
- [ ] Configure Google Calendar API
- [ ] Implement Google authentication
- [ ] Add extracted events to Google Calendar
- [ ] Prevent duplicate calendar entries
- [ ] Handle calendar API errors

## Phase 8 — Testing & Reliability

- [ ] Create `tests/fixtures/`
- [ ] Add direct-PDF test case
- [ ] Add redirect test case
- [ ] Add new-tab test case
- [ ] Add scanned-document test case
- [ ] Add irrelevant-notice test case
- [ ] Add relevant-notice test case
- [ ] Add multiple-dates test case
- [ ] Add malformed/unavailable-document test case
- [ ] Test duplicate notices
- [ ] Test LLM extraction failures
- [ ] Test end-to-end pipeline
- [ ] Test against multiple notice-page structures

## Phase 9 — Hackathon Demo Preparation

- [ ] Prepare a reliable demo dataset
- [ ] Prepare multiple test scenarios
- [ ] Ensure the demo does not depend entirely on a live website
- [ ] Add clear error handling
- [ ] Prepare setup instructions
- [ ] Prepare a short demo flow
- [ ] Verify the complete end-to-end pipeline
- [ ] Test the project on a clean environment
- [ ] Document known limitations

## Phase 10 — Generalization

- [ ] Separate website-specific logic from the core pipeline
- [ ] Support different notice-page structures
- [ ] Improve document retrieval fallback logic
- [ ] Add support for additional document formats
- [ ] Improve extraction reliability
- [ ] Evaluate performance across multiple college websites
