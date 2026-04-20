# Hackathon POC: AI-Powered Compliance Paperwork Automation

**Project Name**: My Compliance Paperwork - Intelligent Document Validation
**Date**: April 2026
**Team**: CBRE Innovation Hackathon 2026

---

## EXECUTIVE SUMMARY

Build an AI-powered system that automatically validates statutory PPM compliance documents, extracts key fields, detects remedial actions, and routes to appropriate systems - eliminating 80%+ of manual review work while maintaining audit compliance.

**Value Proposition**:
- Reduce document processing time from 10-15 minutes to <2 minutes
- Auto-approve 80%+ of documents with 85%+ confidence
- Zero false negatives on critical remedial actions
- Full audit trail with AI decision transparency

**Demo Goal**: Working end-to-end system deployed on Azure with live document processing

---

## PROBLEM STATEMENT

CBRE facilities management teams manually process hundreds of statutory PPM (Planned Preventive Maintenance) compliance documents monthly. Vendors submit diverse formats (PDFs, photos, Word docs) via Smartsheet, and compliance officers must:
1. Manually validate each document (correct site, PPM type, dates)
2. Apply naming conventions
3. Classify as pass (satisfactory) or requires remedial action
4. Upload satisfactory docs to elog books repository
5. Create corrective actions in IFM Hub for failures
6. Update separate compliance tracker spreadsheet

**Pain Points**: Bottlenecks, inconsistencies, delays in identifying critical safety issues

---

## SOLUTION OVERVIEW

An intelligent document processing pipeline that:
1. **Ingests** vendor documents from Smartsheet (webhook/polling)
2. **Extracts** structured data using Azure Document Intelligence
3. **Validates** fields against metadata using GPT-4 agents
4. **Detects** remedial actions via NLP analysis
5. **Scores** confidence and routes automatically
6. **Enables** human override via dashboard
7. **Tracks** analytics and accuracy

**User Journey**: Vendor uploads → AI processes → Officer reviews dashboard → Approve/override → Auto-routes to elog books/IFM Hub

---

## RECOMMENDED TECHNOLOGY STACK

### AI/ML Layer
- **Primary LLM**: Azure OpenAI GPT-4o (extraction, validation) - Fast, cheap, good JSON mode
- **Fallback LLM**: Azure OpenAI GPT-4-turbo (remedial detection) - Better reasoning if needed
- **Document OCR**: Azure Document Intelligence - Layout detection, table extraction
- **Prompts**: Custom Python templates (no framework overhead)

### Backend
- **Runtime**: Azure Functions (Python 3.11) - Serverless, auto-scale, free tier
- **Storage**: Blob (documents) + Table Storage (metadata) - Cheapest option
- **Triggers**: Timer (poll) + Queue (process) + HTTP (API)

### Frontend
- **Framework**: React 18 + Vite
- **UI**: Tailwind CSS + shadcn/ui - Rapid prototyping
- **PDF Viewer**: react-pdf
- **State**: TanStack Query + Context
- **Hosting**: Azure Static Web Apps - Free tier with CI/CD

### Cost Projection (24hr hackathon)
- Azure OpenAI: $1-3
- Document Intelligence: $5-10
- Functions/Storage/Static Web: Free tier
- **Total: $10-15** ✓ Well within $200 credits

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation (Hours 1-8) *parallel work*

**Tasks**:
1. Set up Azure resources — **Cloud Architect**
2. Create sample documents — **UX/BA Lead**
3. Build Azure Function scaffolding — **Backend Lead**
4. Test Document Intelligence API — **AI Engineer**

**Technology Decisions**:
| Component | Options | Chosen | Why |
|-----------|---------|--------|-----|
| OCR | Azure DI / Tesseract | **Azure DI** | Better layout, tables |
| Backend | Functions / Container Apps | **Functions** | Free tier, simple |
| Storage | Table / SQL / Cosmos | **Table Storage** | Cheapest for POC |
| Frontend Host | Static Web / App Service | **Static Web Apps** | Free, auto-deploy |

---

### Phase 2: AI Intelligence (Hours 9-16)

**Tasks**:
5. Extraction agent prompts — **Backend Lead + AI Engineer**
6. Validation agent prompts — **Backend Developer**
7. Remedial detection agent — **Backend Lead**
8. Confidence scoring — **AI Engineer**
9. Table Storage schema — **Backend Developer**

**LLM Model Comparison**:

| Model | Pros | Cons | Cost | Use Case |
|-------|------|------|------|----------|
| **GPT-4o** | 2x faster, 50% cheaper, good JSON | Slightly lower reasoning | $2.50/1M tokens | ✅ Extraction, Validation |
| GPT-4-turbo | Best reasoning, 128k context | Slower (3-5s), expensive | $10/1M tokens | Remedial (fallback) |
| Claude 3.5 | Low hallucination, good following | Separate integration | $3/1M tokens | Alternative |
| Llama 3.1 70B | No per-token cost, privacy | GPU needed, slower | $48/24hr GPU | If budget limited |

**Final Recommendation**:
- Start with **GPT-4o** for all 3 agents
- If remedial detection accuracy <90%, switch that agent to GPT-4-turbo
- Estimated cost for 20 demo docs: **$0.50-2.00 total**

**Framework Decision**:
| Option | Pros | Cons | Chosen |
|--------|------|------|--------|
| Semantic Kernel | Microsoft native, planners | Learning curve, heavy | ❌ |
| LangChain | Popular, many integrations | Overkill for 3 agents | ❌ |
| **Custom Templates** | Full control, lightweight | Manual orchestration | ✅ Best for hackathon |

---

### Phase 3: Frontend (Hours 17-24) *parallel*

**Tasks**:
10. React dashboard skeleton — **UX/BA Lead**
11. Document cards with color coding — **Frontend Developer**
12. Validation screen + PDF viewer — **Frontend Developer**
13. API integration — **Frontend Developer**
14. Override workflow — **Full Stack Developer**

**UI Framework Decision**:
| Option | Pros | Cons | Chosen |
|--------|------|------|--------|
| Fluent UI 2 | Microsoft design, accessible | Large bundle, learning curve | ❌ |
| Material-UI | Popular, React-native | Heavier | ❌ |
| **Tailwind + shadcn/ui** | Fast dev, customizable, small | Need design sense | ✅ Best balance |

---

### Phase 4: Integration & Polish (Hours 25-36)

**Tasks**:
15. Smartsheet integration/mock — **Backend Lead**
16. Analytics calculations — **Backend Developer**
17. End-to-end testing — **All Team**
18. Performance optimization — **Backend Lead**
19. Azure deployment — **Cloud Architect**

**Integration Decision**:
| Option | Pros | Cons | Chosen |
|--------|------|------|--------|
| Smartsheet Webhook | Real-time, no polling | Requires admin access | ❌ Too risky |
| API Polling (5min) | Simple, read-only | Slight delay | ⚠️ Fallback |
| **Manual Upload UI** | Works without access, demo-friendly | Not "real" integration | ✅ Safest for demo |

**Recommendation**: Build upload UI with "Imported from Smartsheet" label, explain webhook for production

---

### Phase 5: Demo Prep (Hours 37-48)

**Tasks**:
20. Demo script (5 min) — **Product Manager**
21. Pre-load data, warm services — **Cloud Architect**
22. Backup video — **UX/BA Lead**
23. Judge Q&A prep — **All Team**
24. Full rehearsal — **All Team**

---

## TEAM ROLE ASSIGNMENTS

**Minimum Team: 4 people** (combine roles below)

| Role | Responsibilities | Can Combine With |
|------|------------------|------------------|
| **Product** | Success criteria, demo narrative, judge Q&A | UX/BA Lead |
| **UX/BA** | Figma, sample docs, frontend components, video | Product Manager |
| **Backend** | Architecture, agent prompts, confidence logic, delegation | AI Engineer |
| **AI Engineer** | Azure OpenAI/DI integration, model testing, prompt optimization | Backend Lead |
| **Cloud- devops** | Azure provisioning, deployment, cost monitoring | Backend Developer |
| **Frontend** | React dashboard, PDF viewer, UI components | Full Stack |
| **Backend** | Azure Functions, Table Storage, validation agent | Cloud Architect |
| **Full Stack** | Smartsheet/upload, override workflow, E2E testing | Frontend |

**Recommended 4-Person Team**:
1. Product Manager + UX/BA Lead
2. Backend Lead + AI Engineer
3. Cloud Architect + Backend Developer
4. Frontend Developer + Full Stack Developer

---

## ALTERNATIVE TECHNOLOGY STACKS

### Alt Stack 1: "Microsoft All-In" (Enterprise Production)
- **When**: Corporate compliance critical, budget available
- **Stack**: GPT-4-turbo, Semantic Kernel, Fluent UI 2, Container Apps, SQL DB, Azure AD
- **Cost**: ~$50-100/month production

### Alt Stack 2: "Open Source Maximum" (Learning/Cost Focus)
- **When**: No vendor lock-in, minimal cost
- **Stack**: Llama 3.1 (self-hosted), Tesseract, FastAPI, PostgreSQL, Vercel
- **Cost**: Free (GPU credits) OR $20/month

### Alt Stack 3: "Hybrid Performance" (Best Accuracy)
- **When**: Accuracy > cost for POC
- **Stack**: Claude 3.5 Sonnet, Azure DI, AWS Lambda, DynamoDB, Next.js
- **Cost**: ~$25-40 for hackathon

---

## ✅ VERIFICATION & DEMO CHECKLIST

### Functional Testing
- [ ] 5 pass documents → All auto-approved with >85% confidence
- [ ] 3 remedial documents → All flagged, issues extracted correctly
- [ ] 1 override → Status updates persist
- [ ] Analytics dashboard → Counts accurate
- [ ] Edge cases (corrupted PDF, wrong type) → Graceful failure

### Performance Testing
- [ ] 20 documents → All process within 2 min each
- [ ] Azure costs → Under $10 total

### Demo Rehearsal
- [ ] Full workflow in <5 minutes
- [ ] Answer "What if AI is wrong?" → Show override
- [ ] Quantify impact: "Saves 24 hours/month per officer"

---

## 🚧 RISKS & MITIGATION

| Risk | Mitigation | Fallback |
|------|------------|----------|
| **Smartsheet access not granted** | Start with manual upload UI | Label as "from Smartsheet", explain webhook for prod |
| **Document formats too varied** | Low confidence → manual review | Collect overrides, refine prompts |
| **Azure costs exceed credits** | Limit to 20-30 demo documents | Use GPT-3.5-Turbo for non-critical agents |
| **Document Intelligence latency** | Pre-process demo docs | Show processing animation, use smaller PDFs |
| **Live demo service timeout** | Pre-load data in Table Storage | Have backup video ready |

**Minimal Viable Demo** (if time-crunched):
1. Manual upload interface
2. Show AI processing
3. Display extractions + remedial classification with confidence
4. Demonstrate override workflow
5. (Skip analytics if needed)

---

## 📊 SUCCESS METRICS

**Demo Success**:
- ✅ End-to-end flow: Upload → AI Process → Review → Override → Route
- ✅ Live on Azure with shareable URL
- ✅ 80%+ accuracy on sample documents
- ✅ Clear confidence scores and reasoning shown
- ✅ Professional UI matching Figma designs

**Business Success** (Post-Hackathon):
- 80%+ automation rate on real documents
- 90%+ accuracy with <10% override rate
- 10x time savings (10min → <1min per document)
- $50k+ annual savings per compliance officer (time value)

---

## 📅 NEXT ACTIONS

### UX/BA Lead:
1. Finalize Figma verbiage based on this plan
2. Get Smartsheet access from business stakeholders
3. Create 5-10 anonymized sample documents (mix of pass/remedial)
4. Document expected fields per document type

### Backend Lead:
1. Design detailed architecture diagram with data flows
2. Create phase-wise task breakdown with hourly estimates
3. Set up GitHub repository structure
4. Define API contracts (OpenAPI spec)

### AI Engineer:
1. Research Azure Document Intelligence pricing/quotas
2. Test extraction with sample PDFs
3. Draft initial extraction agent prompts
4. Compare GPT-4o vs GPT-4-turbo on samples

### Cloud Architect:
1. Set up Azure resource group
2. Configure storage accounts, verify free tier limits
3. Create service principals for CI/CD
4. Document deployment & rollback process

### Product Manager:
1. Schedule mid-sprint architecture review call (Tuesday recommended)
2. Define demo script and judging talking points
3. Create timeline with milestones
4. Prepare backup plans for risks

### All Team:
1. Review this plan, provide feedback
2. Identify missing requirements or blockers
3. Confirm tool access (Azure, Smartsheet, GitHub)
4. Block calendar for hackathon focused time

---

## NEXT MEETING (Suggested: Tuesday Mid-Sprint)

**Agenda**:
1. Review detailed architecture diagram (15 min)
2. Finalize technology stack decisions (10 min)
3. Assign specific tasks with time estimates (15 min)
4. Set up development environment together (20 min)
5. Q&A, blockers, risks (10 min)

**Pre-work**: All team members review this document and come with questions

---

## 📚 REFERENCE MATERIALS

**Existing Project Files**:
- [csv_headers_summary.txt](csv_headers_summary.txt) - Smartsheet field reference (PPM_Ref, Site, Vendor)
- [config/config.yaml](config/config.yaml) - Store Azure connection strings, API keys
- [requirements.txt](requirements.txt) - Add: azure-functions, azure-storage-blob, azure-ai-formrecognizer, openai

**New Files to Create**:
- `src/agents/extraction\\\\\\\_agent.py` - GPT-4 field extraction
- `src/agents/validation\\\\\\\_agent.py` - Metadata cross-check
- `src/agents/remedial\\\\\\\_detection\\\\\\\_agent.py` - Pass/fail classification
- `src/functions/smartsheet\\\\\\\_poller.py` - Timer trigger
- `src/functions/document\\\\\\\_processor.py` - Queue trigger
- `src/functions/api\\\\\\\_gateway.py` - HTTP endpoints
- `frontend/src/components/DocumentCard.jsx`
- `frontend/src/components/ValidationScreen.jsx`
- `demo\\\\\\\_samples/` - Anonymized test documents

---

## JUDGE Q&A PREP

**Q: What if the AI makes a mistake?**
A: We have confidence scoring on every decision. Officers review anything <85% confidence. They can override with one click, and we track that as feedback to improve the prompts. Zero false negatives on critical safety issues is our #1 priority.

**Q: How much does this save?**
A: Officers currently spend 10-15 min manually reviewing each document. With 80% auto-approval at <2 min processing time, we save ~24 hours per month per officer. That's $50k+ annual value in time savings, plus faster identification of critical safety issues.

**Q: Can this work with other document types?**
A: Yes! The same pattern works for any semi-structured compliance document. We use Azure Document Intelligence for layout extraction and prompt engineering to adapt to different document formats. It's a framework, not a one-off solution.

**Q: Why not just use manual review?**
A: Volume is growing, consistency is hard with human review, and compliance officers should focus on critical remedial actions, not validating site names and dates. AI handles the repetitive work, humans handle the nuanced decisions.

**Q: What about production deployment?**
A: This POC proves the concept. Production would add: Smartsheet webhooks for real-time processing, Active Directory auth, direct API integration with elog books and IFM Hub for automated routing, and expanded document types. We'd also collect human overrides to continuously improve via prompt refinement or fine-tuning.

---

**Document Version**: 1.0
**Last Updated**: April 20, 2026
**Status**: Ready for Team Review
