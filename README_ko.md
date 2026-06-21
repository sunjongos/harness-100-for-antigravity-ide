# Harness 100 for Antigravity IDE 🚀

이 프로젝트는 일상생활과 업무에 바로 적용할 수 있는 **100가지 에이전트 팀 하네스 컬렉션**에 **Antigravity IDE** 최적화 병렬 오케스트레이션 엔진과 시각적 대시보드를 이식한 포크 버전입니다.

각 하네스는 에이전트 팀 기능을 활용하여 도메인 전문가 4~5명이 협업하는 프로덕션급 워크플로우를 구성하며, Antigravity IDE 내부에서 백그라운드 프로세스 및 하드웨어(TPU/SSD) 가속을 연동하여 구동됩니다.

---

## ⚡ Antigravity IDE 통합 핵심 기능

1. **병렬 오케스트레이션 엔진 (`luca_parallel_orchestrator.py`)**
   - **Gemini API 기반 동적 컴파일**: 하네스 명세 및 스킬 파일을 Gemini API(`response_mime_type="application/json"`)를 통해 읽어 DAG(방향성 비순환 그래프) 실행 계획으로 즉시 파싱합니다.
   - **스레드 병렬 실행 가속**: 의존 관계가 없는 에이전트 단계(예: 대본 작성과 썸네일 디자인)를 동시에 실행하여 전반적인 수행 소요 시간을 50% 이상 절감합니다.
   - **하드웨어 가속 연동**:
     - **Google Coral Edge TPU**: 이미지/비주얼 관련 태스크 수행 시 TPU 추론 흐름을 실시간 감지하여 최적화 및 로깅을 지원합니다.
     - **Samsung T9 SSD**: Direct I/O 및 Sector-Aligned 스토리지 쓰기 흐름을 연동하여 고속 병렬 디스크 I/O 병목을 최소화합니다.
   - **메모리 및 지식 그래프 동기화**: 모든 작업 결과물과 실행 통계를 로컬 해마 메모리 서버(ASMR 포트 5050) 및 Neo4j 그래프 데이터베이스(bolt://localhost:7687)에 자동으로 파싱하여 동기화합니다.

2. **온톨로지 기반 콘텍스트 자동 주입 (Ontology-driven Context Injection)**
   - 실행 시점에 Neo4j Ontology Graph(기존 실행 기억, 에이전트 노드, 엔티티 노드) 및 옵시디언 장기공유메모리 폴더(`장기공유메모리/luca_brain_memory/`)에서 현재 태스크와 연관성이 높은 핵심 맥락을 추출하여, 모든 에이전트 프롬프트에 자동으로 연동하고 지식을 주입합니다.

3. **자율 하이브리드 하네스 실시간 설계기 (Generative Custom Harness Creator)**
   - 입력된 하네스 쿼리가 `"custom"`이거나 기존 100종의 하네스 폴더 중 일치하는 항목이 없을 때, Gemini 2.5를 통해 최적화된 3~5인 전문 에이전트 팀과 DAG 워크플로우 단계를 실시간으로 동적 컴파일(`custom_harness_config.json`)하여 완전히 새로운 과업 솔루션을 즉석에서 실행합니다.

4. **시각적 관제 대시보드 (`harness_dashboard.html`)**
   - Premium Dark Mode 및 Glassmorphism UI 디자인을 반영하여, 100대 하네스 목록과 실행 명령을 편리하게 관리할 수 있습니다.
   - **Vis.js 대화형 네트워크 뷰**: 각 하네스의 에이전트 팀 협업 구도(Orchestrator ↔ Teammate ↔ Synthesizer) 및 결과 온톨로지를 물리 엔진 기반의 동적 노드 맵으로 시각화하여 탐색할 수 있습니다.

5. **Antigravity 전용 커스텀 스킬 (`.agent/skills/luca_harness_engine/SKILL.md`)**
   - Antigravity IDE 내의 에이전트(LUCA 등)가 대표님의 "HARNESS로 작업해줘"라는 자연어 명령을 받으면, 자동으로 본 오케스트레이터를 호출해 연쇄 태스크를 자율 수행할 수 있도록 설계된 행동 강령입니다.

---

## 🏃 퀵 스타트 & 사용법

### 1. 환경 설정
프로젝트 루트 폴더에 `.env` 파일을 생성하고 다음과 같이 기입합니다 (샘플 양식은 `.env.example` 참조):
```env
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j Graph DB Config (선택사항)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 2. CLI 실행 예시
원하는 하네스의 번호/이름과 태스크 세부 지침을 명령행에 전달하여 즉시 수행할 수 있습니다.
```bash
# 47-strategy-framework 하네스를 기동하여 남양주백병원 전략 수립 진행
python luca_parallel_orchestrator.py --harness "47-strategy-framework" --task "남양주백병원의 2026년 AI 기반 디지털 전환(DT) 및 브랜딩 성장 전략 수립. SWOT 분석, BSC 성과 지표, OKR 로드맵을 통합 수립해줘."
```

### 3. 산출물 확인
작업이 완료되면 `_workspace/` 폴더 내에 순차적으로 넘버링된 결과 파일(마크다운 형태)과 전체 실행 리포트(`run_result.json`)가 영구 보존됩니다.

---

## 📂 프로젝트 구조

```
harness-100-antigravity/
├── luca_parallel_orchestrator.py        # Antigravity 병렬 오케스트레이터 코어
├── harness_dashboard.html               # Premium HTML 시각화 대시보드
├── .env.example                         # 환경 설정 템플릿
├── .agent/
│   └── skills/
│       └── luca_harness_engine/
│           └── SKILL.md                 # Antigravity IDE AI 행동 스킬
├── ko/                                  # 한국어 하네스 100종 (01~100)
├── en/                                  # 영어 하네스 100종 (01~100)
└── README.md
```

## 🛠️ 하네스 100종 카테고리 개요

| 카테고리 | 하네스 범위 | 주요 하이라이트 |
|----------|-------------|-----------------|
| 1. 콘텐츠 제작 & 크리에이티브 | 01 ~ 15 | YouTube 기획, 팟캐스트, 게임 스토리, 광고 카피, 비주얼 스토리텔링 |
| 2. 소프트웨어 개발 & DevOps | 16 ~ 30 | 풀스택 웹앱, API 설계, CI/CD, 코드 리뷰, 보안 감사, 성능 최적화 |
| 3. 데이터 & AI/ML | 31 ~ 42 | ML 실험, 텍스트 처리, RAG/LLM 앱 빌더, BI 대시보드 |
| 4. 비즈니스 & 전략 | 43 ~ 55 | 스타트업 BM, 시장 조사, OKR/BSC 전략 프레임워크, 가격 모델링 |
| 5. 교육 & 학습 | 56 ~ 65 | 언어 튜터, 시험 대비, 토론 시뮬레이터, 지식베이스 구축 |
| 6. 법률 & 규정 | 66 ~ 72 | 계약서 분석, 특허 명세서, GDPR/PIPA 컴플라이언스, 인허가 서류 |
| 7. 건강 & 라이프스타일 | 73 ~ 80 | 식단/운동 프로그램, 세금 계산, 여행 계획, 은퇴 설계 |
| 8. 커뮤니케이션 & 문서 | 81 ~ 88 | 기술 문서 작성, SOP 절차서, 제안서, 위기 대응 메시지 |
| 9. 운영 & 프로세스 | 89 ~ 95 | 채용 파이프라인, 임직원 온온딩, 업무 매뉴얼, 구매 문서 |
| 10. 전문 도메인 | 96 ~ 100 | 부동산 입지 분석, 이커머스 상세페이지, ESG 감사, IP 포트폴리오 |

---

## ⚖️ 라이선스

Apache License 2.0 — 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하십시오.
