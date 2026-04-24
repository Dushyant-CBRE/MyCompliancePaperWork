# Frontend Architecture — CBRE Compliance Paperwork

> AI-powered PPM compliance document processing POC.
> Built for CBRE Innovation Hackathon 2026.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build tool | Vite 8 (`@vitejs/plugin-react`) |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite` plugin) |
| Routing | react-router-dom v6 |
| Icons | lucide-react |
| Charts | recharts (`BarChart`, `LineChart`, `ResponsiveContainer`) |
| Font | Inter (Google Fonts) |
| Formatter | Prettier |

---

## File Structure

```
frontend/
├── src/
│   ├── main.tsx                    # App entry point — mounts <App /> into #root
│   ├── App.tsx                     # BrowserRouter + Routes only (no JSX logic)
│   ├── index.css                   # Tailwind entry, CBRE design tokens, global reset
│   │
│   ├── types/
│   │   └── index.ts                # Shared TypeScript types (DocStatus, Document, Severity, Exception, AuditEntry, ExtractedField, ValidationCheck, RemedialEvidence, ReviewDocument)
│   │
│   ├── lib/
│   │   └── constants.ts            # Shared constants (PIPELINE_STAGES, Stage type)
│   │
│   ├── components/                 # Reusable UI components
│   │   ├── Header.tsx              # Top bar: search, bell, user avatar
│   │   ├── Layout.tsx              # Shell: SideNav + Header + <Outlet />
│   │   ├── SideNav.tsx             # Left sidebar with NavLink navigation
│   │   ├── PageHeader.tsx          # h1 + subtitle — used on every page
│   │   ├── StatCard.tsx            # Single KPI card (label / value / change)
│   │   ├── StatusBadge.tsx         # Auto-Approved / Needs Review / Remedial pill
│   │   ├── ConfidenceBar.tsx       # Progress bar + % text, colour-coded by threshold
│   │   │
│   │   ├── upload/                 # Upload page sub-components
│   │   │   ├── DropZone.tsx        # Drag-and-drop area + Browse Files button
│   │   │   ├── UploadPipelineCard.tsx  # Animated stage-by-stage progress card
│   │   │   └── MetadataForm.tsx    # Optional metadata inputs (site, PPM, vendor, date)
│   │   │
│   │   ├── dashboard/              # Dashboard page sub-components
│   │   │   ├── StatCards.tsx       # 4-column grid of <StatCard>
│   │   │   ├── ProcessingPipeline.tsx  # Horizontal pill steps with connectors
│   │   │   ├── DocumentsTable.tsx  # Toolbar + sortable table of documents
│   │   │   └── BatchApproveModal.tsx   # Confirmation modal for batch approval
│   │   │
│   │   ├── exceptions/             # Exceptions page sub-components
│   │   │   ├── ExceptionStatCards.tsx  # 3-column grid: Critical / Unassigned / SLA Breach
│   │   │   └── ExceptionCard.tsx   # Per-exception card: severity badge, SLA clock, assignee
│   │   │
│   │   ├── settings/               # Settings page sub-components
│   │   │   ├── ThresholdsCard.tsx  # Synced range+number inputs for auto-approve / review
│   │   │   ├── NamingConventionCard.tsx  # Monospace pattern input + checkbox
│   │   │   ├── RemedialDetectionCard.tsx # Keywords textarea + block-approval checkbox
│   │   │   ├── RoutingCard.tsx     # Two destination selects (approved / rejected)
│   │   │   └── RolesCard.tsx       # Static roles list with permission badges
│   │   │
│   │   ├── auditlog/               # Audit Log page sub-components
│   │   │   ├── AuditToolbar.tsx    # Search input + Filter + Export buttons
│   │   │   └── AuditTable.tsx      # Full table with action colour helper + initials avatar
│   │   │
│   │   └── analytics/              # Analytics page sub-components
│   │       ├── AnalyticsStatCards.tsx  # 4 KPI tiles (processing time, approve rate, etc.)
│   │       ├── ProcessingLineChart.tsx # recharts LineChart — documents processed per hour
│   │       ├── ConfidenceBarChart.tsx  # recharts BarChart — confidence score distribution
│   │       ├── SiteBreakdownTable.tsx  # Per-site counts with inline progress bar column
│   │       ├── QualitySafetyCard.tsx   # False negative rate + remedial + evidence metrics
│   │       └── PPMDistributionCard.tsx # 4 PPM types with horizontal coloured bars
│   │
│   ├── documentreview/             # DocumentReview page sub-components
│   │   ├── DocumentReviewHeader.tsx    # Sticky top bar: back, doc name/meta, AI badges, SLA, 4 action buttons, confidence bar
│   │   ├── PDFViewerPanel.tsx      # Left panel: zoom/rotate toolbar + aspect-ratio PDF placeholder
│   │   ├── AnalysisPanel.tsx       # Right panel shell: 4-tab bar + renders active tab component
│   │   ├── ExtractedFieldsTab.tsx  # Field rows: label, value, source, mini confidence bar, decorative Edit2
│   │   ├── ValidationChecksTab.tsx # Pass/fail rows with CheckCircle2 / XCircle icons, green/red backgrounds
│   │   ├── RemedialDetectionTab.tsx    # Red alert banner + per-evidence severity cards
│   │   ├── AuditReasoningTab.tsx   # Read-only AI reasoning: decision, timing, confidence breakdown
│   │   └── OverrideModal.tsx       # Fixed overlay: reason select, comments textarea, training checkbox
│   │
│   └── pages/                     # Route-level orchestrators (thin, state-only)
│       ├── Dashboard.tsx           # / route
│       ├── Upload.tsx              # /upload route
│       ├── Exceptions.tsx          # /exceptions route
│       ├── Settings.tsx            # /settings route
│       ├── AuditLog.tsx            # /audit route
│       ├── Analytics.tsx           # /analytics route
│       └── DocumentReview.tsx      # /document/:id route
│
├── .prettierrc                     # Formatting config
├── .vscode/settings.json           # Editor config (format on save, tab size)
├── vite.config.ts                  # Vite + Tailwind v4 plugin
├── tsconfig.app.json               # TypeScript strict config
└── index.html                      # HTML shell with #root mount point
```

---

## Architecture

### Routing

Routes are defined once in `App.tsx`. All authenticated pages share the `<Layout />` shell via React Router's `<Outlet />` pattern — the shell renders once, only the `<main>` content swaps.

```
BrowserRouter
└── Routes
    └── <Layout />          (SideNav + Header + main)
        ├── /               → <Dashboard />
        ├── /upload         → <Upload />
        ├── /exceptions     → <Exceptions />
        ├── /analytics      → <Analytics />
        ├── /audit          → <AuditLog />
        ├── /settings       → <Settings />
        └── /document/:id   → <DocumentReview />
```

> **Layout exception**: `DocumentReview` uses `h-full flex flex-col` instead of the standard `p-6` scroll wrapper. The left (PDF) and right (analysis) panels each manage their own `overflow-auto` independently. All other pages use a `p-6` wrapper that scrolls as one unit.

### Component Responsibility Model

Each layer has a single job:

| Layer | Responsibility |
|---|---|
| **Page** (`pages/`) | Own state, event handlers, mock/fetched data. No markup beyond a wrapper `<div>`. |
| **Section component** (`components/dashboard/`, `components/upload/`) | Receive props, render a self-contained section of a page. No state. |
| **Shared component** (`components/`) | Pure presentational. Accept minimal, typed props. Used across multiple pages. |

This means pages stay thin (30–55 lines) and every visual section is independently testable and replaceable.

### Data Flow

State lives at the page level and is passed **down** as props. No global state manager is used — the app is simple enough for prop drilling.

```
Dashboard.tsx
  showBatchModal (useState)
  ├── <StatCards />                    (no props — renders static mock)
  ├── <ProcessingPipeline />           (no props — renders static mock)
  ├── <DocumentsTable
  │       documents={mockDocuments}
  │       onApproveAll={...} />
  └── <BatchApproveModal
          eligibleCount={...}
          onClose={...}
          onConfirm={...} />
```

```
Upload.tsx
  uploadProgress, isProcessing, isDragOver (useState)
  ├── <DropZone onDrop onDragOver onDragLeave onFileSelect isDragOver />
  ├── <UploadPipelineCard currentStage={uploadProgress} />   (conditional)
  └── <MetadataForm />                                        (no props)
```

```
Exceptions.tsx
  mockExceptions[] (static)
  ├── <ExceptionStatCards />                  (no props — static counts)
  └── mockExceptions.map → <ExceptionCard exception={e} />
```

```
Settings.tsx
  autoApprove, manualReview (useState — controls threshold sliders)
  ├── <ThresholdsCard autoApprove manualReview onAutoApproveChange onManualReviewChange />
  ├── <NamingConventionCard />        (uncontrolled — defaultValue)
  ├── <RemedialDetectionCard />       (uncontrolled — defaultValue)
  ├── <RoutingCard />                 (uncontrolled — defaultValue)
  ├── <RolesCard />                   (no props — static)
  └── Save / Reset to Defaults buttons
```

```
AuditLog.tsx
  mockAuditEntries[] (static)
  ├── <AuditToolbar />                (no props — decorative search/filter)
  ├── <AuditTable entries={mockAuditEntries} />
  └── Pagination footer (static)
```

```
Analytics.tsx
  processingData[], confidenceDistribution[], siteBreakdown[] (static)
  ├── <AnalyticsStatCards />          (no props — static)
  ├── <ProcessingLineChart data={processingData} />
  ├── <ConfidenceBarChart data={confidenceDistribution} />
  ├── <SiteBreakdownTable data={siteBreakdown} />
  ├── <QualitySafetyCard />           (no props — static)
  └── <PPMDistributionCard />         (no props — static)
```

```
DocumentReview.tsx
  useParams() → id
  activeTab (useState: 'fields' | 'validation' | 'remedial' | 'audit')
  showOverrideModal (useState)
  mockDoc, mockFields[], mockChecks[], mockEvidence[] (static)
  ├── <DocumentReviewHeader doc={mockDoc} id={id} onOverride={...} />
  ├── (flex-1 flex overflow-hidden)
  │   ├── <PDFViewerPanel fileName={mockDoc.name} />
  │   └── <AnalysisPanel
  │           activeTab onTabChange
  │           fields={mockFields}
  │           checks={mockChecks}
  │           evidence={mockEvidence} />
  └── {showOverrideModal && <OverrideModal onClose={...} />}   (fixed overlay)
```

---

## Styling System

### Tailwind CSS v4

No `tailwind.config.js`. Everything is config-file-free:

- `@import "tailwindcss"` in `index.css` replaces the three legacy directives
- `@tailwindcss/vite` plugin in `vite.config.ts` replaces the PostCSS setup
- `@theme inline {}` block maps CSS custom properties to Tailwind utility names

### CBRE Design Tokens

All brand colours are defined as CSS custom properties in `index.css :root` and exposed to Tailwind via `@theme inline`:

| Token | Value | Usage |
|---|---|---|
| `--primary` | `#003F2D` | Dark green — buttons, sidebar, rings |
| `--accent` | `#17E88F` | CBRE green — success states, confidence ≥85% |
| `--destructive` | `#d4183d` | Red — notification dot, error states |
| `--foreground` | `#435254` | Body text |
| `--muted-foreground` | `#717182` | Secondary / placeholder text |
| `--muted` | `#F6F8F7` | Input backgrounds, table header fill |
| `--sidebar` | `#003F2D` | Sidebar background |
| `--sidebar-foreground` | `#ffffff` | Sidebar text |

Tailwind utilities like `bg-primary`, `text-accent`, `border-sidebar-border` work because of the `@theme inline` mapping.

### Confidence Colour Thresholds

Applied in `ConfidenceBar.tsx` and `StatusBadge.tsx`:

| Range | Colour | Meaning |
|---|---|---|
| ≥ 85% | `bg-accent` (CBRE green) | Auto-approved |
| 70–84% | `bg-yellow-400` | Needs review |
| < 70% | `bg-red-400` | High risk / remedial |

### Global Reset

CSS reset lives inside `@layer base` in `index.css`. This ensures Tailwind's cascade layers take priority — placing it outside any layer would silently override all utility classes.

```css
@layer base {
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', system-ui, sans-serif; }
}
```

---

## Coding Standards

### Formatting (Prettier)

Enforced via `.prettierrc` and VS Code `formatOnSave`:

```json
{
    "tabWidth": 4,
    "useTabs": false,
    "singleQuote": true,
    "semi": true,
    "trailingComma": "es5",
    "printWidth": 100
}
```

### TypeScript

- `verbatimModuleSyntax` is enabled — types must use `import type` syntax:
  ```ts
  import type { DocStatus } from '../types';
  ```
- All component props are typed with an explicit `interface`
- Shared types live in `src/types/index.ts`; shared constants in `src/lib/constants.ts`

### recharts Usage

recharts does not read CSS custom properties — chart colours must use raw hex values:

| Purpose | Value |
|---|---|
| Line/bar stroke | `#003F2D` (= `--primary`) |
| Grid lines | `#e5e7eb` |
| Axis labels | `#9ca3af` |

All chart components use `<ResponsiveContainer width="100%" height={250}>` to fill their parent card.

### Component Conventions

- Named exports only — no default exports from components
- One component per file, filename matches the exported function name
- Props interfaces are defined inline above the component, not in a separate types file
- `lucide-react` icons are sized with Tailwind (`w-4 h-4`, `w-5 h-5`) — never inline style

### File Naming

| Pattern | Example |
|---|---|
| Components | `PascalCase.tsx` |
| Sub-component folders | `lowercase/` |
| Types / constants | `camelCase.ts` |
| Pages | `PascalCase.tsx` |

---

## Features Implemented

### Dashboard (`/`)
- **Stat cards** — 4 KPI tiles: Total Documents, Auto-Approved, Needs Review, Remedial Detected
- **Processing pipeline** — visual 5-step flow: Imported → OCR / Extracted → Validated → Remedial Check → Routed
- **Documents table** — sortable list with Status badge, Confidence bar, flag pills
- **Batch approve modal** — warns the user before approving all docs with confidence ≥85%

### Upload / Import (`/upload`)
- **Drag-and-drop zone** — accepts PDF, JPG, PNG, DOCX; highlights on hover/drag
- **Animated pipeline card** — simulates 5 processing stages with spinner / checkmark animation
- **Optional metadata form** — Site, PPM Type, Vendor, Document Date; pre-filled with "Auto-detect"
- **Open Review CTA** — appears when pipeline reaches "Completed" stage

### Exceptions Queue (`/exceptions`)
- **Stat cards** — 3 tiles: Critical Items (red), Unassigned (muted), SLA Breach Risk (orange)
- **Exception cards** — one card per exception: severity badge, 4-col detail grid (Vendor / PPM / Reason / Confidence bar), SLA clock, assignee chip or "Assign to Me" CTA
- Critical exceptions render a red alert banner at the top of the card

### Settings (`/settings`)
- **Confidence Thresholds** — synced range slider + number input for Auto-Approve (85%) and Manual Review (70%) thresholds; range ↔ number stay in sync via controlled `useState`
- **Naming Convention Rules** — monospace pattern input + flag checkbox
- **Remedial Detection** — keywords textarea + block-approval checkbox
- **Routing Destinations** — two selects: approved routing and rejection action
- **User Roles & Permissions** — static table of 3 roles with permission badge pills
- **Reset to Defaults** — resets threshold state back to 85 / 70

### Audit Log (`/audit`)
- **Toolbar** — decorative search input + Filter and Export buttons
- **Table** — 6 columns: Timestamp (date + time stacked), User (avatar initials + name), Action (colour-coded pill), Document (truncated filename), Details (detail + optional Reason line), Training (blue chip when `trainingFeedback` is true)
- **Action colour map** — Auto-Approved/Batch Approve → green, Override → yellow, Reject → red, Remedial Detected → orange
- **Pagination footer** — static "Showing 5 of 1,247 entries" + Previous/Next buttons

### Analytics & Accuracy (`/analytics`)
- **KPI stat cards** — 4 tiles: Avg Processing Time, Auto-Approve Rate, Override Rate, Critical Alerts
- **Documents Processed (24h)** — recharts `LineChart` over 6 time-of-day buckets
- **Confidence Distribution** — recharts `BarChart` over 5 confidence-score ranges
- **Breakdown by Site** — table with per-site approved/review/remedial counts + inline mini progress bar for auto-approve %
- **Quality & Safety** — False Negative Rate (green highlight), Critical Remedial Detected, Evidence Highlights
- **PPM Type Distribution** — 4 horizontal bars (Fire Safety / Electrical / HVAC / Elevator) with distinct colours

### Document Review (`/document/:id`)
- **Sticky header bar** — back button (→ `/`), filename + site/PPM type/ID meta row, AI Decision + Risk Level badges, SLA clock, 4 action buttons (Approve / Override / Request Resubmission / Reject), inline confidence bar
- **Split-panel layout** — left: PDF viewer with zoom/rotate toolbar and aspect-ratio placeholder; right: 480px analysis panel
- **4-tab analysis panel**:
  - *Extracted Fields* — 6 field rows each with label, extracted value, source citation, mini accent confidence bar, and decorative Edit2 pencil
  - *Validation Checks* — pass (green / CheckCircle2) and fail (red / XCircle) rows; fail rows show detail sub-text
  - *Remedial Detection* — red alert banner + per-evidence cards coloured by severity (High → red, Medium → yellow)
  - *Audit & Reasoning* — read-only AI card: model decision, processing time, timestamp, confidence breakdown table
- **Override modal** — fixed `z-50` overlay with reason select, free-text comments textarea, training-feedback checkbox; Submit and Cancel both close the modal in POC

---

## Pages Yet to Be Implemented

| Route | Page | Notes |
|---|---|---|
| `/login` | Login | Authentication page |

> **Immutability constraint (for future backend wiring)**: In `DocumentReview`, `ai_description` is read-only and must never appear in any PATCH/PUT body. Only `reviewer_description` is editable. The Edit2 pencil icon in `ExtractedFieldsTab` is currently decorative.
