# FinOps Study Platform — Project Status

> Last updated: 2026-03-17

## Overview

CLI 기반 `finops_sim` 엔진(40개 시나리오)을 **스터디 그룹용 웹 플랫폼**으로 확장.
DB/서버 없이 **GitHub Pages + GitHub Actions + repo**를 저장소로 활용.

- **스터디 repo**: `cloud-club/09th-ai-cloud-finops` (6~10명)
- **디자인 참고**: CupixWorks V5 (좌측 사이드바, 밝은 테마, 그라데이션 카드)

---

## Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Frontend    │────▶│  GitHub API     │────▶│  GitHub Repo │
│  (Pages)     │     │  (REST v3)      │     │  (Storage)   │
└──────────────┘     └─────────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │ GitHub Actions│
                                              │ (Compute)    │
                                              └──────────────┘
```

| 역할 | 기술 |
|------|------|
| 프론트엔드 | Vanilla JS + CSS (GitHub Pages) |
| 인증 | GitHub PAT (localStorage) |
| 문제 생성 | Python scripts (finops_sim 엔진 래핑) |
| 정답 보안 | 지연 생성 (reveal_date에 시드 재생성) |
| 답안 제출 | GitHub Issues + Contents API (파일 업로드) |
| 채점 | 키워드 매칭 (4영역 × 30-20-30-20점) |
| 개인화 | sha256(username:week:GROUP_SALT) 시드 |

---

## Implementation Status

### ✅ Completed (2026-03-17)

#### Phase A: Backend Scripts + Workflows
| File | Description |
|------|-------------|
| `config/group.yaml` | 그룹 설정 + admin 목록 |
| `config/members.yaml` | 멤버 등록 (GitHub username) |
| `config/weeks/week-01.yaml` | 주차별 설정 |
| `scripts/generate_week.py` | 시드 기반 멤버별 문제 생성 |
| `scripts/reveal_answers.py` | 정답 재생성 (reveal_date) |
| `scripts/parse_submission.py` | Issue body → JSON + TF 파일 저장 |
| `scripts/score_submissions.py` | 키워드 매칭 채점 + 리더보드 |
| `.github/workflows/generate-weekly.yaml` | 관리자 수동 트리거 |
| `.github/workflows/reveal-answers.yaml` | 매일 09:00 KST cron |
| `.github/workflows/process-submission.yaml` | Issue 생성 트리거 |
| `.github/workflows/score-week.yaml` | 정답 공개 후 채점 |
| `.github/ISSUE_TEMPLATE/submission.yaml` | 구조화 이슈 템플릿 |

#### Phase B-E: Frontend (CupixWorks V5 Style)
| File | Description |
|------|-------------|
| `frontend/index.html` | Dashboard (주차 카드, stats, 그라데이션 헤더) |
| `frontend/problems.html` | 문제 조회 (TF, Chart.js 메트릭, 비용 테이블, Hint) |
| `frontend/submit.html` | 3단계 제출 (Analysis + Terraform + Report Upload) |
| `frontend/scores.html` | 리더보드 + 개인 세부 점수 |
| `frontend/admin.html` | 주차 생성, 멤버 관리, 수동 액션 |
| `frontend/css/style.css` | CupixWorks 스타일 (Inter, 밝은 테마) |
| `frontend/js/app.js` | GitHub API 클라이언트 + 로컬 모드 |
| `frontend/js/problems.js` | Chart.js + highlight.js 렌더링 |
| `frontend/js/submit.js` | 파일 업로드 + Issue 생성 |
| `frontend/js/scores.js` | 리더보드 렌더링 |
| `frontend/js/admin.js` | workflow_dispatch 트리거 |

#### Local Test Results
```
✅ generate_week.py --week 1 --level L1 --num-problems 3 → L1-002, L1-010, L1-013
✅ reveal_answers.py --week 1 → answer.json + scoring_rubric.json 재생성
✅ parse_submission.py → Issue body → JSON 파싱 + TF 코드 별도 저장
✅ score_submissions.py --week 1 → 채점 + summary.json 리더보드
✅ 로컬 서버(8080) → 전 페이지 정상 렌더링
```

---

### 🔲 TODO: 배포 준비

| # | Task | Priority |
|---|------|----------|
| 1 | git init + GitHub push | P0 |
| 2 | `GROUP_SALT` 시크릿 등록 (repo Settings > Secrets) | P0 |
| 3 | GitHub Pages 배포 설정 (`frontend/` 디렉토리) | P0 |
| 4 | `config/members.yaml`에 스터디원 추가 | P0 |
| 5 | E2E 테스트 (실제 repo에서 generate → submit → reveal → score) | P1 |
| 6 | `deploy-pages.yaml` 워크플로 추가 | P1 |
| 7 | scripts 유닛 테스트 (pytest) | P2 |
| 8 | 스터디원용 사용 가이드 README | P2 |

---

## Key Design Decisions

### 시드 기반 개인화
```
seed = sha256("{username}:{week}:{GROUP_SALT}") % 2^31
sub_seed = seed + i * 1000  (시나리오별)
```
- 같은 멤버 + 같은 주차 = 항상 같은 문제
- GROUP_SALT은 Actions Secret → 역산 불가

### 정답 보안: 지연 생성
- 문제 생성 시 answer.json 삭제
- reveal_date에 동일 시드로 재생성 → 결정적이므로 동일 결과 보장

### 제출 구조 (3단계)
1. **Analysis** (필수) — 문제식별, 원인, 해결책, 절감액 → Issue body
2. **Terraform** (선택) — 최적화 코드 → `submissions/week-XX/user/scenario/solution.tf`
3. **Report** (선택) — MD/PDF 파일 → `submissions/week-XX/user/scenario/파일명`

---

## Data Flow

```
관리자: Admin → Generate 클릭
  ↓
GitHub Actions: generate-weekly.yaml
  → 멤버별 시드 계산
  → finops_sim 엔진으로 문제 생성
  → problems/ 커밋 (answer 제외)
  ↓
스터디원: Problems 페이지에서 문제 확인
  → Submit 페이지에서 답안 제출
  → Issue 생성 + 파일 커밋 (TF/Report)
  ↓
GitHub Actions: process-submission.yaml
  → Issue 파싱 → submissions/ JSON 커밋
  ↓
reveal_date 도래: reveal-answers.yaml (cron)
  → 동일 시드로 answer 재생성 → answers/ 커밋
  → score-week.yaml 트리거
  ↓
스터디원: Scores 페이지에서 결과 확인
```

---

## Session Logs
- [2026-03-17 — 웹 플랫폼 전체 구현](./logs/2026-03-17_web-platform-implementation.md)
