You are continuing an existing Enterprise AI Research Engine project.

IMPORTANT:
This is NOT a new project.
Do NOT redesign the architecture.
Do NOT modify completed features unless absolutely necessary.
Preserve the existing Clean Architecture, Repository Pattern, Service Layer, Dependency Injection, and coding style.

Current project status:

Backend:
- FastAPI
- SQLAlchemy ORM
- Alembic
- JWT Authentication
- Refresh Tokens
- Users
- Projects
- Audit Logs
- Document Upload
- Document Download
- Document Delete
- Local File Storage
- Repository Pattern
- Service Layer
- 16/16 backend tests passing

Frontend:
- React + Vite
- Document Workspace
- Upload UI
- Download
- Delete
- Responsive Layout
- 7/7 frontend tests passing

Current document lifecycle:

UPLOADED
PROCESSING
PROCESSED
FAILED

======================================================

Implement COMPLETE PHASE 4:
Document Processing Pipeline

Generate EVERYTHING in one implementation.

DO NOT stop after creating a plan.

DO NOT ask for confirmation.

DO NOT create milestones.

Generate every required file.

======================================================

OBJECTIVE

Whenever a document is uploaded:

1. Save metadata.
2. Store the file.
3. Start document processing.
4. Extract text.
5. Store extracted text.
6. Update status.
7. Handle failures.
8. Preserve Clean Architecture.

======================================================

SUPPORTED FILES

PDF
DOCX
TXT
MD

======================================================

TEXT EXTRACTION

Implement extraction services for

PDF using pdfplumber

DOCX using python-docx

TXT using UTF-8 reader

Markdown using UTF-8 reader

Return plain text only.

======================================================

PROCESSING PIPELINE

After upload:

UPLOADED

↓

PROCESSING

↓

Extract Text

↓

Store Extracted Text

↓

PROCESSED

If extraction fails

↓

FAILED

======================================================

DATABASE

Extend existing Document model.

Add only necessary fields.

Possible fields:

processed_at

extracted_text

processing_error

page_count (optional)

word_count (optional)

Do not remove existing columns.

Generate Alembic migration.

Migration must support:

SQLite

PostgreSQL

Downgrade

======================================================

SERVICE LAYER

Create:

DocumentProcessorService

Responsibilities:

Load document

Choose extractor

Extract text

Validate extraction

Update database

Update status

Handle exceptions

No FastAPI dependencies.

No HTTPException.

======================================================

EXTRACTOR LAYER

Create abstraction.

Example:

BaseExtractor

PDFExtractor

DOCXExtractor

TXTExtractor

MarkdownExtractor

Factory pattern preferred.

======================================================

REPOSITORY

Keep database logic inside repository.

No SQL inside services.

======================================================

API

Add processing endpoint if needed.

Do NOT break existing upload endpoint.

Existing endpoints must continue working.

======================================================

ERROR HANDLING

Use domain exceptions.

Map exceptions in FastAPI.

No HTTPException inside services.

======================================================

TESTS

Generate complete tests.

Backend only.

Cover:

PDF extraction

DOCX extraction

TXT extraction

Markdown extraction

Status updates

Failed extraction

Repository updates

Processing service

API endpoint

Migration compatibility

Target:

All tests passing.

Do NOT remove existing tests.

======================================================

QUALITY REQUIREMENTS

Follow existing naming.

Keep imports clean.

No duplicate code.

No dead code.

No TODOs.

No placeholders.

No mocked implementations.

======================================================

OUTPUT FORMAT

Generate every file completely.

Whenever modifying an existing file, output the complete updated file.

Whenever creating a new file, output the complete file.

Do not omit code.

Do not shorten code.

Do not summarize.

Implement the complete phase in one response.

At the end provide:

1. Files modified
2. Files created
3. Database changes
4. New endpoints
5. Commands to run
6. Verification commands
7. Expected pytest result
8. Expected Alembic result

The final implementation must preserve all existing functionality while ensuring all previous tests continue passing and all new tests pass.
