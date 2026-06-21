# Harness 100 for Antigravity IDE 🚀

This is a customized fork of **Harness 100**—a production-grade collection of **100 agent team harnesses**—fully optimized for **Antigravity IDE** with parallel orchestration, hardware acceleration, and an interactive UI dashboard.

Each harness coordinates 4-5 specialist agents cooperating as a high-fidelity team to solve domain-specific tasks. The Antigravity integration enables async execution, hardware pooling (Coral TPU / SSD), and graph synchronization.

---

## ⚡ Antigravity IDE Integration Features

1. **Parallel Orchestrator Engine (`luca_parallel_orchestrator.py`)**
   - **Gemini-Powered DAG Compilation**: Dynamically reads harness specifications and skills using Gemini (`response_mime_type="application/json"`) to map out execution dependencies.
   - **Thread Pool Parallelization**: Executes non-dependent agent steps (e.g., scriptwriting & thumbnail design) concurrently, cutting total pipeline execution time by over 50%.
   - **Hardware Acceleration**:
     - **Google Coral Edge TPU**: Automatically detects and leverages Coral Edge TPU hardware for visual and image-related inference steps.
     - **Samsung T9 SSD**: Configured with Sector-Aligned direct write logs to prevent file system I/O bottlenecks during concurrent generation.
   - **ASMR & Graph DB Sync**: Automatically parses and syncs execution results to the local memory server (ASMR on Port 5050) and Neo4j graph database (bolt://localhost:7687).

2. **Control Dashboard (`harness_dashboard.html`)**
   - Premium Dark Mode and Glassmorphism Web Interface to monitor all 100 harnesses and copy commands.
   - **Vis.js Interactive Graph**: Embedded dynamic node mapping showing the agent topology (Orchestrator ↔ Teammates) using a physics engine.

3. **Antigravity Custom Skill (`.agent/skills/luca_harness_engine/SKILL.md`)**
   - Internal guidelines allowing Antigravity agents (like LUCA) to intercept "HARNESS" queries and automatically launch orchestrator runs.

---

## 🏃 Quick Start & Usage

### 1. Environment Config
Create a `.env` file in the root directory (see `.env.example` for details):
```env
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j Graph DB Config (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 2. Execute via CLI
Pass the harness identifier and your instructions directly:
```bash
python luca_parallel_orchestrator.py --harness "47-strategy-framework" --task "Establish a 2026 digital transformation roadmap for Baek Hospital, including SWOT matrix, BSC metrics, and OKRs."
```

### 3. Review Deliverables
Outputs are sequentially written to the `_workspace/` directory along with a performance summary `run_result.json`.

---

## 📂 Repository Structure

```
harness-100-antigravity/
├── luca_parallel_orchestrator.py        # Antigravity Parallel Orchestrator
├── harness_dashboard.html               # Premium HTML UI Control Panel
├── .env.example                         # Environment template
├── .agent/
│   └── skills/
│       └── luca_harness_engine/
│           └── SKILL.md                 # Antigravity IDE custom skill
├── ko/                                  # Korean Harnesses (01~100)
├── en/                                  # English Harnesses (01~100)
└── README.md
```

---

## 🛠️ Harness Categories At a Glance

| Category | Harnesses | Description |
|----------|-----------|-------------|
| 1. Content & Creative | 01 ~ 15 | YouTube automation, podcast studio, game narrative, comic creator |
| 2. Software Dev & DevOps | 16 ~ 30 | Full-stack webapp, API design, CI/CD pipelines, security audits |
| 3. Data & AI/ML | 31 ~ 42 | ML experiments, RAG application builder, BI dashboards |
| 4. Business & Strategy | 43 ~ 55 | Startup bm validation, market research, SWOT/BSC/OKR framework |
| 5. Education & Learning | 56 ~ 65 | Language tutor, exam prep, debate simulation, knowledge bases |
| 6. Legal & Compliance | 66 ~ 72 | Contract analysis, patent drafting, GDPR compliance |
| 7. Health & Lifestyle | 73 ~ 80 | Meal planning, fitness tracking, personal finance, travel |
| 8. Communication & Docs | 81 ~ 88 | Technical writing, SOP builder, proposal writer, crisis comms |
| 9. Operations & Process | 89 ~ 95 | Hiring pipeline, employee onboarding, operations manual |
| 10. Specialized Domains | 96 ~ 100 | Real estate analyst, e-commerce launch, ESG sustainability |

---

## ⚖️ License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
