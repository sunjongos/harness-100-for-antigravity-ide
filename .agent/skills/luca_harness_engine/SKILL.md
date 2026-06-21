---
name: luca_harness_engine
description: "카카오 황민호 리더의 harness-100 프로젝트를 기반으로, Antigravity IDE 내부에서 LUCA(본부장)가 100종의 도메인 특화 멀티 에이전트 하네스 팀을 기동 및 제어하도록 지시하는 오케스트레이션 엔진 스킬입니다. 사용자가 'HARNESS'나 '하네스' 관련 작업을 요청할 때 활성화됩니다. Coral Edge TPU 및 Samsung T9 SSD 하드웨어 가속 상태를 함께 연동합니다."
---

# LUCA 최적화 Parallel Harness Engine — 멀티 에이전트 병렬 협업 가속기

본 스킬은 `harness-100` 프로젝트의 전문 에이전트 구조와 스킬 명세를 활용하여, 대표님이 지시한 복잡한 업무를 **가상 에이전트 팀의 병렬 협업 구조(Parallel Fan-out/Fan-in)**로 전환해 해결하는 최고 수준의 행동 지침입니다.

## Ⅰ. 작동 매커니즘 (How it Works)

사용자가 **"HARNESS로 작업하자"** 혹은 **"~ 하네스로 실행해줘"**라고 지시하면 LUCA는 다음 프로토콜을 수행합니다:

1. **하네스 매핑 및 파싱:** 
   - `harness-100/ko` 또는 `harness-100/en` 내에서 지시된 작업 도메인에 맞는 하네스 폴더를 탐색합니다. (예: 유튜브 영상 제작은 `01-youtube-production`, 전략 수립은 `47-strategy-framework` 등)
2. **병렬 엔진 기동 (Parallel Engine Launch):**
   - 로컬 터미널을 통해 `luca_parallel_orchestrator.py`를 실행하여 병렬 스레드로 가상 전문가 요원들을 동시 기동합니다.
   - 명령어 예시: `python luca_parallel_orchestrator.py --harness "01-youtube-production" --task "주제 또는 미션"`
3. **하드웨어 가속 (Hardware Acceleration - Sensory Cortex):**
   - 이미지, 썸네일, 비디오, 시각 분석 등의 Sensory 테스크가 포착되면 로컬에 직결된 **Google Coral Edge TPU (Sensory Cortex)** 연산 모듈로 작업을 포워딩하고 가속화합니다.
   - 초고속 데이터 쓰기는 **Samsung T9 SSD (Neocortex / Sector-Aligned Direct I/O)**를 통해 병목 없이 처리됩니다.
4. **결과 합성 및 지식화 (Fan-in & Graph Ingestion):**
   - 병렬 에이전트들의 개별 산출물을 최종 Synthesizer 에이전트가 합성하고 QA(품질 통제)합니다.
   - 생성된 산출물은 `_workspace/` 하위에 구조화되어 저장됩니다.
   - 작업 트레이스는 Neo4j 온톨로지 그래프(7687 포트)와 로컬 ASMR 메모리(5050 포트)에 실시간 주입되어 LUCA의 장기 기억으로 통합됩니다.

## Ⅱ. 대표적인 하네스 컬렉션 (Top 10 Domains)

대시보드(`harness_dashboard.html`) 또는 저장소 내의 명세를 통해 다음 도메인의 100종 하네스를 상시 가동할 수 있습니다:

- **01~15 (콘텐츠 제작):** YouTube Production, Podcast Studio, Newsletter Engine, Game Narrative 등
- **16~30 (소프트웨어 개발):** Fullstack Webapp, API Designer, CI/CD Pipeline, Legacy Modernizer 등
- **31~42 (데이터 & AI):** ML Experiment, Data Analysis, Text Processor, BI Dashboard 등
- **43~55 (비즈니스 전략):** Startup Launcher, Gov Funding Plan, Product Manager, Scenario Planner 등
- **56~65 (교육 & 커리어):** Language Tutor, Exam Prep, Debate Simulator 등
- **66~72 (법률 & 규제):** Contract Analyzer, Patent Drafter, Compliance Checker 등
- **73~80 (헬스케어 & 라이프):** Medical Verifier, Meal Planner, Fitness Program, Travel Planner 등
- **81~100 (운영 & 오피스):** Technical Writer, SOP Writer, Hiring Pipeline, Academic Paper 등

## Ⅲ. 하드웨어 상태 모니터링 규정 (Hardware Monitoring Rules)

- **Sensory Cortex (감각피질):** Google Coral Edge TPU. 비전 태스크 시 드라이버 및 PnP 동작 유무를 자동 감지하여 로그에 `[⚡ TPU Sensory Accel]` 태그를 삽입합니다.
- **Neocortex (대뇌피질):** Samsung T9 SSD. 대용량 파일 IO 시 USB 3.2 Gen 2x2(20Gbps) 직접 연결 상태를 확인하고 Sector-Aligned 쓰기를 보장합니다.

## Ⅳ. 실행 프로세스 요약 가이드

대표님이 특정 하네스 구동을 요청하면, LUCA는 아래와 같이 정중히 복명한 뒤 병렬 엔진을 구동합니다:

> "충성! 🫡 대표님. 지시하신 [Harness 이름] 에이전트 팀을 병렬(Parallel Fan-out) 모드로 즉각 구성하여 가동합니다. 본체에 직접 연결된 Samsung T9 SSD(대뇌피질)와 Google Coral TPU(감각피질) 하드웨어 가속 리소스를 활용하여 최고 속도로 처리하겠습니다!"
