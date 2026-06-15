# Migration Guide: Azure OpenAI & LLM-Based Architecture

## Overview

This document describes the refactoring from a complex multi-service architecture to a **simple, unified LLM-based approach** using only **Azure OpenAI**, **Azure Storage**, and configuration-driven field extraction.

---

## What Changed

### Removed Services

| Service | Reason | Impact |
|---------|--------|--------|
| **Anthropic Claude (Azure AI Foundry)** | Resource optimization; Azure OpenAI sufficient | All LLM operations now use Azure OpenAI |
| **Azure AI Content Understanding** | Complex, limited benefit; LLM Vision works well | Replaced with Azure OpenAI Vision for OCR |
| **Azure Document Intelligence** | Expensive; LLM-based extraction more flexible | Removed from pdf_extractor fallback chain |

### New Architecture

```
┌─ Document Upload ────────────────────────────────────────┐
│                                                           │
├─ PDF → Text Extraction                                   │
│  ├─ PyMuPDF (embedded text)                             │
│  └─ Azure OpenAI Vision (for scanned/image-only PDFs)   │
│                                                           │
├─ Config-Driven Field Extraction                          │
│  └─ YAML config defines all fields, prompts, rules      │
│                                                           │
├─ Azure OpenAI LLM Agents (Orchestration Loop)            │
│  ├─ Agent 1: Field Extraction (config-driven)           │
│  ├─ Agent 2: Validation (cross-check vs metadata)       │
│  └─ Agent 3: Remedial Detection (compliance status)     │
│                                                           │
├─ Confidence Scoring & Routing                            │
│  └─ AUTO_APPROVED / MANUAL_REVIEW / REQUIRES_ATTENTION  │
│                                                           │
└─ Azure Storage (Blob + Table)                            │
   └─ PDF, extracted text, metadata, audit logs            │
```

---

## File Changes Summary

### Configuration & Infrastructure

#### [backend/config.py](backend/config.py)
- **Removed**: `anthropic_*`, `wso2_*`, `azure_content_understanding_*` settings
- **Added**: `azure_openai_api_key`, `azure_openai_endpoint`, `azure_openai_deployment_id`
- **Added**: `field_config_path`, `llm_temperature`, `llm_max_retries`
- All settings now read from `.env` file

#### [backend/.env.example](backend/.env.example)
- **Completely rewritten** with clear documentation
- Now focuses on: Azure OpenAI credentials, Storage connection, Processing thresholds, LLM settings
- Removed all Anthropic and Content Understanding references

#### [backend/requirements.txt](backend/requirements.txt)
- **Removed**: `anthropic>=0.49.0`, `azure-ai-contentunderstanding>=1.0.0`, `azure-identity>=1.17.0`
- **Added**: `pyyaml>=6.0` (for field configuration)
- **Kept**: `openai>=1.30.1` (Azure OpenAI SDK is part of this)

### New Configuration System

#### [backend/data/field_extraction_config.yaml](backend/data/field_extraction_config.yaml)
**New file** that defines:
- All extractable fields (name, type, description, extraction prompt, examples, validation rules)
- Compliance classification rules (patterns for PASS, NON_COMPLIANT, REMEDIAL)
- Remedial detection configuration and urgency levels
- Global extraction settings (temperature, retries, etc.)

This allows updating field definitions **without code changes**.

#### [backend/utils/field_config.py](backend/utils/field_config.py)
**New module** that:
- Loads and parses the YAML configuration
- Provides `FieldConfig` class for individual fields
- Exposes `ExtractionConfigManager` singleton
- Generates dynamic prompts and JSON schemas from config

---

### LLM Client Refactoring

#### [backend/utils/llm_client.py](backend/utils/llm_client.py)
**Completely rewritten** - was 246 lines of Anthropic wrapper, now:
- Direct Azure OpenAI SDK integration
- Simplified retry logic (exponential backoff)
- Handles tool calling for agentic operations
- Single `AzureOpenAIClient` class replacing `AnthropicFoundryClient`

**Key improvements:**
- Fewer dependencies
- Cleaner error handling
- Native Azure OpenAI support (no proxy)

---

### PDF Extraction Simplified

#### [backend/services/pdf_extractor.py](backend/services/pdf_extractor.py)
- **Removed**: Content Understanding prebuilt analyzer step
- **Kept**: PyMuPDF for embedded text (fast, works well)
- **Updated**: Vision fallback now uses Azure OpenAI Vision (not Claude)
- Cleaner 2-level fallback: `PyMuPDF → Azure OpenAI Vision`

**Result:** Same functionality, simpler code, one LLM provider

---

### Config-Driven Agents

#### [backend/agents/extraction_agent.py](backend/agents/extraction_agent.py)
**Major refactor** from hardcoded fields to:
- Dynamically loads field definitions from `field_extraction_config.yaml`
- Generates extraction prompts at runtime based on config
- **System prompt built from config** (no hardcoding)
- Each field includes: name, type, description, extraction hints, examples

**Benefits:**
- Add new fields by editing YAML only
- Update extraction prompts without code changes
- Consistent field handling across all agents

#### [backend/agents/validation_agent.py](backend/agents/validation_agent.py)
- No code changes (already generic)
- Uses extracted fields and optional metadata for validation
- Produces match scores and issues list

#### [backend/agents/remedial_agent.py](backend/agents/remedial_agent.py)
- No code changes (already generic)
- Deterministic checks + LLM classification
- Returns: PASS / REMEDIAL_MINOR / REMEDIAL_CRITICAL

#### [backend/agents/orchestrator.py](backend/agents/orchestrator.py)
- **Removed**: Pre-extracted fields logic (was checking for Content Understanding results)
- Now simpler: always starts with `extract_all_fields` tool
- Agentic loop: extract → validate → detect → finalize

---

### Document Processing Pipeline

#### [backend/services/document_processor.py](backend/services/document_processor.py)
- **Removed**: Step 2a (Content Understanding custom analyzer call)
- **Simplified** to 5-step pipeline:
  1. Upload PDF to Blob Storage
  2. Extract text (PyMuPDF or Azure OpenAI Vision)
  3. Run Orchestrator (agents)
  4. Calculate confidence score
  5. Generate insights
  
---

## Configuration Migration

### Old Environment (.env)
```bash
# Old – Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_ENDPOINT=...

# Old – Content Understanding
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=...
AZURE_CONTENT_UNDERSTANDING_KEY=...

# Old – Proxy
WSO2_AUTH_URL=...
```

### New Environment (.env)
```bash
# New – Simple Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_ID=<deployment-name>

# Storage (unchanged)
AZURE_STORAGE_CONNECTION_STRING=...

# LLM Settings
LLM_TEMPERATURE=0.2
LLM_MAX_RETRIES=2

# Field Configuration
FIELD_CONFIG_PATH=data/field_extraction_config.yaml
```

---

## How to Customize

### Adding a New Field

1. Open `backend/data/field_extraction_config.yaml`
2. Add to `document_types.compliance_certificate.fields`:

```yaml
- name: new_field_name
  type: string              # or date, array
  required: true
  description: "What this field is"
  extraction_prompt: |
    Instructions for LLM to extract this field...
  examples:
    - "Example 1"
    - "Example 2"
  validation_rules:
    min_length: 1
    max_length: 100
  fallback_value: null      # or default value
  confidence_field: true    # include in scoring?
```

3. The extraction agent will automatically:
   - Include it in extraction prompts
   - Request confidence scores
   - Add it to JSON schema
   - No code changes needed!

### Adjusting Extraction Behavior

Edit `backend/data/field_extraction_config.yaml`:
- **extraction_settings**: global temperature, retries, thresholds
- **compliance_classification**: patterns for PASS/REMEDIAL/NON_COMPLIANT
- **remedial_detection**: urgency levels and rules

### Changing LLM Model

Update `.env`:
```bash
AZURE_OPENAI_DEPLOYMENT_ID=gpt-4-turbo  # or gpt-35-turbo, etc.
```

That's it! The system automatically uses it for all operations.

---

## Breaking Changes

### For Code Integrations

1. **LLM Client Import**: 
   ```python
   # Old
   from backend.utils.llm_client import AnthropicFoundryClient
   
   # New
   from backend.utils.llm_client import AzureOpenAIClient
   ```

2. **Config Access**:
   ```python
   # Old
   settings.anthropic_api_key
   settings.azure_content_understanding_endpoint
   
   # New
   settings.azure_openai_endpoint
   settings.azure_openai_deployment_id
   settings.field_config_path
   ```

3. **Field Config**:
   ```python
   # New utility
   from backend.utils.field_config import get_field_config_manager
   
   manager = get_field_config_manager()
   fields = manager.get_all_fields()
   ```

### For Operations

1. **No more Content Understanding setup** – just Azure OpenAI
2. **No more Azure AI Foundry configuration** – simplified
3. **Field definitions live in YAML** – update without deploying code

---

## Deployment Checklist

- [ ] Install new dependencies: `pip install -r backend/requirements.txt`
- [ ] Copy `.env.example` to `.env` and fill in Azure OpenAI credentials
- [ ] Ensure `backend/data/field_extraction_config.yaml` exists
- [ ] Test field extraction: run pytest on extraction_agent
- [ ] Verify Azure Storage connection works
- [ ] Check orchestrator runs end-to-end
- [ ] Update any documentation referencing old services

---

## Benefits of This Architecture

✅ **Simpler**: One LLM provider (Azure OpenAI)  
✅ **Cheaper**: No Content Understanding subscription  
✅ **Flexible**: Field definitions in YAML (no code changes)  
✅ **Faster**: Fewer service calls, direct LLM + Storage  
✅ **Maintainable**: Clear separation of concerns  
✅ **Scalable**: Easy to add new fields or change prompts  
✅ **Auditable**: All field definitions centralized  

---

## Next Steps

1. **Update your `.env`** with Azure OpenAI credentials
2. **Test field extraction** with sample documents
3. **Customize `field_extraction_config.yaml`** for your document types
4. **Adjust confidence thresholds** if needed
5. **Monitor LLM usage** via Azure OpenAI dashboards (cheaper than before!)

---

## Support & Questions

- Field extraction not finding values? → Check extraction prompts in YAML
- Compliance classification wrong? → Review remedial_detection rules in YAML
- Want to add a field? → Just edit the YAML, no code changes needed!
