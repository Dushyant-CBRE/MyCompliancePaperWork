## 🎨 Mermaid Diagrams (Auto-Render in GitHub/VS Code)
  

### **Diagram 1: High-Level System Architecture**

  

```mermaid
graph TB
    subgraph Vendor["🏢 External Systems"]
        SS[Smartsheet<br/>Vendor Submissions]
        MU[Manual Upload<br/>Web Form]
    end

  

    subgraph Azure["☁️ Azure Cloud Platform"]

        subgraph Ingestion["📥 Ingestion Layer"]

            F1[Azure Function 1<br/>Smartsheet Poller<br/>Timer: 5min]

            BLOB[Azure Blob Storage<br/>documents/]

            Q[Storage Queue<br/>processing-queue]

        end

  

        subgraph Processing["🤖 AI Processing Layer"]

            F2[Azure Function 2<br/>Document Processor]

            DI[Azure Document<br/>Intelligence<br/>OCR/Layout]

            subgraph Agents["AI Agent Pipeline"]

                A1[Agent 1: Extraction<br/>GPT-4o<br/>Extract Fields]

                A2[Agent 2: Validation<br/>GPT-4o<br/>Cross-check]

                A3[Agent 3: Remedial<br/>GPT-4o/4-turbo<br/>Classify Pass/Fail]

            end

            CONF[Confidence Score<br/>Calculation]

        end

  

        subgraph Storage["💾 Data Storage"]

            TABLE[Table Storage<br/>Document Metadata]

        end

  

        subgraph API["🔌 API Layer"]

            F3[Azure Function 3<br/>API Gateway<br/>REST Endpoints]

        end

  

        subgraph Monitor["📊 Monitoring"]

            AI[Application Insights<br/>Logs & Metrics]

        end

    end

  

    subgraph Frontend["🖥️ Frontend Layer"]

        SWA[Azure Static Web App<br/>React 18 + Vite]

        subgraph Components["UI Components"]

            C1[Upload Dashboard]

            C2[Validation Screen]

            C3[Remedial Dashboard]

            C4[Analytics]

        end

    end

  

    subgraph Downstream["📤 Future Integrations"]

        ELOG[elog books<br/>Pass Documents]

        IFM[IFM Hub<br/>Remedial Actions]

    end

  

    %% Flow connections

    SS -->|PDF/Images| F1

    MU -->|Direct Upload| BLOB

    F1 -->|Download| BLOB

    F1 -->|Queue Message| Q

    Q -->|Trigger| F2

    BLOB -.->|Retrieve Doc| F2

    F2 -->|Extract Text| DI

    DI -->|Text + Layout| A1

    A1 -->|Fields + Conf| A2

    A2 -->|Validation| A3

    A3 -->|Classification| CONF

    CONF -->|Results| TABLE

    TABLE -->|Query| F3

    F3 <-->|HTTPS REST| SWA

    SWA --> C1

    SWA --> C2

    SWA --> C3

    SWA --> C4

    F2 -.->|Logs| AI

    F3 -.->|Metrics| AI

    TABLE -.->|Future| ELOG

    TABLE -.->|Future| IFM

  

    style Vendor fill:#e1f5ff

    style Azure fill:#fff4e6

    style Frontend fill:#f3e5f5

    style Downstream fill:#e8f5e9

    style Agents fill:#fff9c4

    style DI fill:#ffccbc

    style A1 fill:#c5e1a5

    style A2 fill:#c5e1a5

    style A3 fill:#c5e1a5

```

  

---

  

### **Diagram 2: Document Processing Sequence (Happy Path)**

  

```mermaid

sequenceDiagram

    actor Vendor

    participant SS as Smartsheet

    participant F1 as Function 1<br/>Poller

    participant Blob as Blob Storage

    participant Q as Queue

    participant F2 as Function 2<br/>Processor

    participant DI as Document<br/>Intelligence

    participant GPT as GPT-4o<br/>Agents

    participant Table as Table Storage

    participant API as API Gateway

    participant UI as React Dashboard

    actor Officer

  

    Vendor->>SS: Upload PPM Document (PDF)

    Note over SS: Document stored in Smartsheet

    loop Every 5 minutes

        F1->>SS: Poll for new documents

    end

    SS-->>F1: New document found

    F1->>Blob: Download & store PDF

    F1->>Q: Enqueue {doc_id, metadata}

    Note over Q: Message triggers Function 2

    Q->>F2: Trigger with message

    F2->>Blob: Retrieve PDF

    Blob-->>F2: PDF bytes

    F2->>DI: Extract text & layout

    DI-->>F2: Structured text + tables

    Note over F2,GPT: AI Agent Pipeline (Sequential)

    F2->>GPT: Agent 1: Extract fields

    GPT-->>F2: {site: "A" (95%), ppm: "1234" (98%), ...}

    F2->>GPT: Agent 2: Validate fields

    GPT-->>F2: {site_match: 100%, ppm_match: 100%}

    F2->>GPT: Agent 3: Detect remedial

    GPT-->>F2: {classification: PASS, conf: 92%}

    Note over F2: Calculate confidence: 95%<br/>Decision: AUTO_APPROVE

    F2->>Table: Store result {status: approved, conf: 95%}

    loop Every 10 seconds

        UI->>API: GET /api/documents

    end

    API->>Table: Query documents

    Table-->>API: Document list

    API-->>UI: JSON response

    UI->>Officer: Display green card<br/>"Auto-approved (95%)"

    Officer->>UI: Click to view details

    UI->>API: GET /api/documents/123

    API->>Table: Fetch details

    Table-->>API: Full document data

    API-->>UI: Detailed JSON

    UI->>Officer: Show PDF + AI analysis

```

  

---

  

### **Diagram 3: AI Agent Pipeline (Detailed)**

  

```mermaid
flowchart TD
    Start([Document PDF]) --> DI[Azure Document Intelligence<br/>OCR + Layout Analysis]
    
    DI --> Text[Extracted Text<br/>+ Table Data<br/>+ Key-Value Pairs]
    
    Text --> Agent1
    
    subgraph Agent1["🤖 Agent 1: Extraction (GPT-4o)"]
        A1P[Prompt: Extract these fields:<br/>• Site Name<br/>• PPM Reference<br/>• Date<br/>• Inspector<br/>• Equipment ID]
        A1E[LLM Extract with<br/>JSON Mode]
        A1O["Output:<br/>field: value, confidence: %"]
        A1P --> A1E --> A1O
    end
    
    Agent1 --> Agent2
    
    subgraph Agent2["🤖 Agent 2: Validation (GPT-4o)"]
        A2P[Prompt: Compare extracted<br/>vs expected metadata]
        A2C[Cross-check:<br/>Site match?<br/>PPM ref match?<br/>Date valid?]
        A2O["Output:<br/>match_scores: %"]
        A2P --> A2C --> A2O
    end
    
    Agent2 --> Agent3
    
    subgraph Agent3["🤖 Agent 3: Remedial Detection (GPT-4o)"]
        A3P[Prompt: Analyze findings<br/>for remedial actions]
        A3S[Scan for:<br/>• fail keywords<br/>• action required<br/>• deficiencies]
        A3C{Classification}
        A3O1[PASS<br/>No issues]
        A3O2[REMEDIAL_MINOR<br/>Advisory]
        A3O3[REMEDIAL_CRITICAL<br/>Failed compliance]
        A3P --> A3S --> A3C
        A3C --> A3O1
        A3C --> A3O2
        A3C --> A3O3
    end
    
    A3O1 --> Conf
    A3O2 --> Conf
    A3O3 --> Conf
    
    Conf[Calculate Overall Confidence<br/>weighted_avg = 30% extract +<br/>30% validation + 40% remedial]
    
    Conf --> Decision{Confidence<br/>Score?}
    
    Decision -->|>= 85%| Auto[AUTO_APPROVE<br/>✅ Green Card]
    Decision -->|60-85%| Review[MANUAL_REVIEW<br/>⚠️ Yellow Card]
    Decision -->|< 60%| Attn[REQUIRES_ATTENTION<br/>🔴 Red Card]
    
    Auto --> Save[(Table Storage)]
    Review --> Save
    Attn --> Save
    
    Save --> End([Dashboard Display])
    
    style Agent1 fill:#c8e6c9
    style Agent2 fill:#c8e6c9
    style Agent3 fill:#c8e6c9
    style DI fill:#ffccbc
    style Auto fill:#a5d6a7
    style Review fill:#fff59d
    style Attn fill:#ef9a9a
```

---


  

---

  

### **Diagram 4: Data Model (Entity Relationship)**

  

```mermaid

erDiagram

    DOCUMENT ||--o{ EXTRACTED_FIELD : contains

    DOCUMENT ||--o| REMEDIAL_ANALYSIS : has

    DOCUMENT ||--o| HUMAN_OVERRIDE : may_have

    DOCUMENT {

        string PartitionKey "YYYYMM"

        string RowKey "doc_uuid"

        string ppm_ref

        string site

        string vendor

        datetime upload_date

        string document_blob_path

        string status "pending/approved/overridden"

        float overall_confidence

        string ai_classification "PASS/REMEDIAL_MINOR/CRITICAL"

    }

    EXTRACTED_FIELD {

        string field_name "site, ppm_ref, date, etc"

        string extracted_value

        float confidence

        boolean matches_expected

    }

    REMEDIAL_ANALYSIS {

        string classification

        float confidence

        json issues "array of issue descriptions"

        string reasoning

    }

    HUMAN_OVERRIDE {

        string officer_id

        string new_classification

        string reason

        datetime override_date

    }

```

  

---

  


```mermaid

flowchart LR

    Dev[👨‍💻 Developer] -->|git push| GH[GitHub Repository]

    GH -->|Webhook| GHA[GitHub Actions<br/>Workflow]

    subgraph Pipeline["🔄 CI/CD Pipeline"]

        GHA --> Build[Build & Test]

        Build --> Deploy

        subgraph Deploy["Deploy Stage"]

            D1[Deploy Functions<br/>to Azure Function App]

            D2[Deploy Frontend<br/>to Static Web App]

        end

    end

    Deploy --> Azure[☁️ Azure Resources]

    subgraph Azure["Azure Environment"]

        FA[Function App<br/>func-document-processor]

        SWA[Static Web App<br/>stapp-compliance-dashboard]

    end

    Azure -->|Live URL| Users[👥 End Users]

    style Deploy fill:#e1f5fe

    style Azure fill:#fff3e0

```

  



### **Diagram : Alternative Architecture Options**

  

```mermaid

graph LR

    subgraph Current["Option A: Serverless (Recommended)"]

        AF[Azure Functions]

        TS[Table Storage]

        BL[Blob Storage]

    end

    subgraph Alt1["Option B: Container-Based"]

        ACA[Container Apps<br/>FastAPI]

        SQL[Azure SQL DB]

        BL2[Blob Storage]

    end

    subgraph Alt2["Option C: Local Development"]

        PY[Python Scripts]

        SQLITE[SQLite DB]

        FS[File System]

    end

    Current -.->|"If need complex<br/>business logic"| Alt1

    Current -.->|"For rapid<br/>iteration"| Alt2

    Alt2 -.->|"For production<br/>deployment"| Current

    style Current fill:#a5d6a7

    style Alt1 fill:#fff59d

    style Alt2 fill:#90caf9

```

  

---

  

## 📖 How to View Mermaid Diagrams

  

### **In GitHub**

✅ Renders automatically when you view the file on GitHub.com

  

### **In VS Code**

1. Install extension: "Markdown Preview Mermaid Support"

2. Open this file

3. Press `Ctrl+Shift+V` (Preview)

4. Diagrams render inline

  

### **Export to Image**

1. Use https://mermaid.live/

2. Paste diagram code

3. Export as PNG/SVG for presentations

  

---

  

**Diagram Version**: 1.0  

**Last Updated**: April 20, 2026  

**Status**: Ready for Architecture Review
