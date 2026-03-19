# FinOps AI Agent — Starter Kit

FinOps 문제를 분석하는 AI 에이전트의 기본 뼈대입니다.

## 구조

```
starter-kit/
├── agent.py              ← 메인 에이전트 (이것만 실행하면 됨)
├── config.py             ← 모델 설정 (Ollama/OpenAI/Claude 전환)
├── file_reader.py        ← 문제 파일 파싱 (main.tf, metrics.json 등)
├── output_builder.py     ← 출력 JSON 생성 + 스키마 검증
├── prompts/
│   ├── system.md         ← 시스템 프롬프트 (FinOps 전문가 역할)
│   ├── L1_analyze.md     ← L1 분석 프롬프트
│   ├── L2_analyze.md     ← L2 분석 프롬프트 (+ 단위경제)
│   └── L3_analyze.md     ← L3 분석 프롬프트 (+ 알림 생성)
└── requirements.txt      ← 의존성
```

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Ollama 설치 + 모델 다운로드 (로컬 모델 사용 시)
# https://ollama.com 에서 설치
ollama pull llama3.1        # 8B (가벼움, 빠름)
ollama pull qwen2.5:14b     # 14B (성능 좋음, 추천)

# 3. 문제 분석 실행
python agent.py ./path/to/problem/L1-001/

# 4. 출력 검증
python agent.py ./path/to/problem/L1-001/ --validate-only
```

## 모델 설정

`config.py`에서 사용할 모델을 선택합니다.

### Ollama (로컬, 무료)
```python
MODEL_PROVIDER = "ollama"
MODEL_NAME = "qwen2.5:14b"    # 또는 llama3.1, mistral 등
OLLAMA_URL = "http://localhost:11434"
```

### OpenAI API
```python
MODEL_PROVIDER = "openai"
MODEL_NAME = "gpt-4o-mini"    # 저렴한 옵션
OPENAI_API_KEY = "sk-..."
```

### Claude API
```python
MODEL_PROVIDER = "claude"
MODEL_NAME = "claude-sonnet-4-20250514"
ANTHROPIC_API_KEY = "sk-ant-..."
```

## 동작 흐름

```
1. 문제 폴더 읽기
   ├── main.tf          → Terraform 리소스 파싱
   ├── metrics.json     → 메트릭 시계열 요약 (평균, 최대, 최소, 0% 비율)
   ├── cost_report.json → 비용 추이 + 낭비 서비스 식별
   ├── business_metrics.json (L2+) → 단위경제 지표
   └── tags_inventory.json (L2+) → 태그 누락 리소스

2. 프롬프트 조립
   시스템 프롬프트 + 레벨별 분석 프롬프트 + 파일 내용

3. LLM 호출
   Ollama / OpenAI / Claude API 호출

4. 응답 파싱
   LLM 응답에서 JSON 추출 → output_schema.json 검증

5. 출력 저장
   analysis.json 파일로 저장
```

## 커스텀 포인트

에이전트를 개선할 수 있는 방향:

- **프롬프트 튜닝**: prompts/ 폴더의 프롬프트를 수정하여 분석 품질 향상
- **메트릭 분석 강화**: file_reader.py에서 통계 분석 로직 추가 (이동 평균, Z-score 등)
- **다단계 분석**: LLM을 여러 번 호출하여 1차 스캔 → 2차 심층 분석
- **Terraform 파서**: HCL 파서 라이브러리(python-hcl2)로 정확한 리소스 추출
- **비용 계산기**: AWS 요금표 기반으로 절감액 직접 계산
