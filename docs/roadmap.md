# Developer Roadmap

## Phase 1 — Notice Webpage

- [x] Fetch webpage HTML
- [x] Parse HTML
- [x] Identify notice links
- [x] Extract notice metadata
- [x] Test against the NSUT notices page (https://imsnsit.org/imsnsit/notifications.php)
- [x] Test against the IITD notices page (https://academics.iitd.ac.in/circulars/)

## Phase 2 — Notice Tracking

- [x] Detect newly added notices
- [x] Store identifiers for processed notices
- [x] Prevent unnecessary reprocessing
- [x] Test first-run vs subsequent-run behavior

## Phase 3 — Document Retrieval

- [x] Support direct document URLs
- [x] Support redirecting links
- [x] Add browser automation
- [x] Handle documents opened in new tabs
- [x] Handle retrieval failures
- [x] Delete temporary documents after processing

## Phase 4 — AI Processing

- [x] Choose LLM/API
- [x] Define structured output format
- [x] Send documents to the LLM
- [x] Extract dates and times
- [x] Extract relevant notice information
- [x] Determine notice relevance to the student
- [x] Handle scanned documents/images
- [x] Validate structured LLM output

## Phase 5 — Student Profile

- [x] Define student profile fields
- [x] Create profile input/storage
- [x] Use profile information for relevance filtering
- [x] Test relevant vs irrelevant notices

## Phase 6 — User Interface

- [x] Display processed notices
- [x] Display extracted dates/events
- [x] Allow users to view extracted information
- [x] Handle errors clearly

## Phase 7 — Hackathon Demo Preparation

- [x] Prepare a reliable demo dataset
- [x] Add clear error handling
- [x] Prepare setup instructions
- [x] Prepare a short demo flow
- [x] Verify the complete end-to-end pipeline
- [x] Test the project on a clean environment
- [x] Document known limitations

## Phase 8 — Generalization

- [x] Separate website-specific logic from the core pipeline
- [ ] Support different notice-page structures
- [x] Improve document retrieval fallback logic
- [ ] Add support for additional document formats
- [ ] Improve extraction reliability
- [x] Evaluate performance across multiple college websites
