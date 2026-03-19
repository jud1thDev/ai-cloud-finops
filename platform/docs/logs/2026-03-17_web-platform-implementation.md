# 2026-03-17 — FinOps 스터디 웹 플랫폼 구현

## 요약
CLI 기반 `finops_sim` 엔진(40개 시나리오)을 **스터디 그룹용 웹 플랫폼**으로 확장.
DB/서버 없이 GitHub Pages + GitHub Actions + repo를 저장소로 활용하는 구조.

## 완료된 작업

### Phase A: 기반 + 문제 생성 파이프라인
- `config/group.yaml` — 그룹 설정 (repo, admin 목록)
- `config/members.yaml` — 멤버 등록 (GitHub username)
- `config/weeks/week-01.yaml` — 주차별 설정 (level, num_problems, reveal_date)
- `scripts/generate_week.py` — 시드 기반 멤버별 문제 생성 (answer 제외)
  - seed = sha256(username:week:GROUP_SALT) % 2^31
  - 기존 orchestrator._generate_one() 래핑
  - answer.json, scoring_rubric.json 삭제 후 커밋
- `scripts/reveal_answers.py` — reveal_date 도래 시 동일 시드로 정답 재생성
- `scripts/parse_submission.py` — Issue body → JSON 파싱 (Terraform 코드도 별도 저장)
- `scripts/score_submissions.py` — 키워드 매칭 채점 + 리더보드 생성
- `.github/workflows/generate-weekly.yaml` — workflow_dispatch (관리자 수동)
- `.github/workflows/reveal-answers.yaml` — 매일 00:00 UTC cron
- `.github/workflows/process-submission.yaml` — Issue 생성 트리거
- `.github/workflows/score-week.yaml` — 정답 공개 후 채점
- `.github/ISSUE_TEMPLATE/submission.yaml` — 구조화 이슈 템플릿

### Phase B-E: 프론트엔드 (CupixWorks V5 스타일)
**레이아웃**: 좌측 사이드바 + 메인 콘텐츠 (밝은 화이트/그레이 테마)

- `frontend/index.html` — Dashboard (주차 카드 목록, 그라데이션 헤더, stats)
- `frontend/problems.html` — 문제 조회 (README, Terraform, Cost Report 테이블, Metrics 차트, Hint)
- `frontend/submit.html` — 3단계 제출 폼:
  1. Analysis (필수): 문제식별/원인/해결책/절감액
  2. Terraform (선택): 최적화 코드 monospace 에디터
  3. Report Upload (선택): MD/PDF 드래그앤드롭 (5MB, GitHub Contents API 커밋)
- `frontend/scores.html` — 리더보드 + 개인 세부 점수
- `frontend/admin.html` — 주차 생성 UI, 멤버 목록, 제출 현황, 수동 액션
- `frontend/css/style.css` — CupixWorks 스타일 (Inter 폰트, 12px radius, 그라데이션 카드)
- `frontend/js/app.js` — GitHub API 클라이언트, 로컬 모드 지원
- `frontend/js/problems.js` — Chart.js 메트릭 차트, highlight.js TF 구문강조
- `frontend/js/submit.js` — 파일 업로드, Terraform 제출, Issue 생성
- `frontend/js/scores.js` — 리더보드 렌더링
- `frontend/js/admin.js` — workflow_dispatch 트리거

### 로컬 개발 모드
- `APP.LOCAL` 플래그: localhost 접근 시 자동 활성화
- GitHub API 대신 `../` 상대경로로 파일 직접 fetch
- `_index.json` 파일로 디렉토리 리스팅 지원
- 로그인 없이 자동 인증 (leejiseok)

## 로컬 테스트 결과
- `generate_week.py --week 1 --level L1 --num-problems 3` → L1-002, L1-010, L1-013 생성 확인
- `reveal_answers.py --week 1` → answer.json + scoring_rubric.json 재생성 확인
- `parse_submission.py` → Issue body → JSON 파싱 + TF 코드 별도 저장 확인
- `score_submissions.py --week 1` → 채점 + summary.json 리더보드 생성 확인
- 로컬 서버(python3 -m http.server 8080) → 전 페이지 정상 렌더링 확인

## UI 디자인 결정
- **참고 디자인**: CupixWorks V5 (https://cupixworks-v5.web.app)
- 좌측 사이드바 + 아이콘 네비게이션, ADMIN 섹션 분리
- 밝은 테마 (#f5f6fa 배경, #ffffff 카드)
- 그라데이션 카드 헤더 (teal, blue, purple, orange, pink, green)
- pill 스타일 탭, 아바타 + 유저 정보 사이드바 풋터
- Inter 폰트, 12px border-radius, subtle shadow

## 핵심 아키텍처 메모
- **시드 결정성**: 동일 (username, week, salt) → 동일 문제/리소스명/메트릭
  - sub_seed = master_seed + i * 1000 (시나리오별)
- **정답 보안**: problems/에는 answer 없음, reveal_date에 answers/로 재생성
- **GROUP_SALT**: GitHub Actions Secret → 멤버가 시드 역산 불가
- **파일 업로드**: GitHub Contents API로 repo에 직접 커밋 (Issue가 아닌 별도)
- **채점**: 4영역 × 키워드 매칭 (30-20-30-20점 배분)

## 남은 작업
1. **배포 준비**: git init + push, GitHub Pages 설정, GROUP_SALT 시크릿 등록
2. **멤버 등록**: config/members.yaml에 스터디원 추가
3. **E2E 테스트**: 실제 repo에서 전체 흐름 검증
4. **GitHub Pages 배포 workflow**: frontend/ 자동 배포
5. **scripts 유닛 테스트**: pytest 추가
6. **README 업데이트**: 스터디원용 사용 가이드

## 파일 트리 (새로 생성)
```
config/group.yaml
config/members.yaml
config/weeks/week-01.yaml
scripts/generate_week.py
scripts/reveal_answers.py
scripts/parse_submission.py
scripts/score_submissions.py
frontend/index.html
frontend/problems.html
frontend/submit.html
frontend/scores.html
frontend/admin.html
frontend/css/style.css
frontend/js/app.js
frontend/js/problems.js
frontend/js/submit.js
frontend/js/scores.js
frontend/js/admin.js
.github/workflows/generate-weekly.yaml
.github/workflows/reveal-answers.yaml
.github/workflows/process-submission.yaml
.github/workflows/score-week.yaml
.github/ISSUE_TEMPLATE/submission.yaml
```
