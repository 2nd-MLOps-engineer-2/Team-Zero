# 역할 하나를 선택하고 시작하기

## 가장 짧은 시작 방법

1. Codex 또는 Claude Code에서 **Team-Zero 로컬 저장소**를 연다. 아직 없으면 아래 저장소를 복제해 연다.
2. [README 역할 선택](README.md#역할을-선택하고-바로-시작하기)의 자기 역할 코드 블록을 복사해 한 번 전달한다.
3. 에이전트가 해당 역할의 프롬프트·체크북·계획서를 읽고 현재 코드부터 확인한 뒤 구현·검증·인수인계까지 진행한다.

```bash
git clone https://github.com/2nd-MLOps-engineer-2/Team-Zero.git
cd Team-Zero
```

이미 작업 중인 로컬 저장소는 변경을 보존하고 최신 `main`과 비교한다. 사용자 변경을 지우거나 진행 중 브랜치를 초기화하지 않는다. 각 팀원은 자신의 GitHub 계정을 사용한다.

**여기서 '바로 시작'은 역할 프롬프트 하나로 개발을 시작한다는 뜻이다. GitHub 링크를 누르는 것만으로 로컬 에이전트가 자동 실행되거나 서비스가 배포되는 기능은 아니다.**

## 시작할 때 에이전트가 할 일

1. 작업 트리, 브랜치·HEAD, 기존 구현과 실행 환경을 확인한다.
2. 역할에 해당하는 작업 ID·소유 경로·당장 가능한 작업을 짧게 알린다.
3. 기존 환경과 파일을 재사용하며 담당 기능을 구현한다.
   `docs/missing-work.md`의 해당 역할 보완 업무도 수행한다. 없는 문서·계약·구현·검사는 직접 추가하고, 원천 입력이 필요한 부분만 구체적으로 요청한다.
4. 필요한 입력만 구체적으로 묻고, 다른 역할을 기다리는 동안 계약·fixture·샘플·검증을 진행한다.
5. 실제 실행한 검사와 결과를 기록하고 handoff를 남긴다.

## 실제 데이터로 시작하기

**인계 패키지 75파일은 이미 저장소에 포함되어 있다.** `data/03_C_integration_20261014/04_output/silver/`에 Silver 17개, `gold/`에 기존 Gold 2개가 있다. [데이터 상세](docs/data-guide.md)와 [전체 사전](docs/data-catalog.md)을 먼저 읽는다.

```bash
python3 scripts/check_handoff.py
```

Python 표준 기능만으로 파일·해시·CSV 건수를 확인한다. 원본을 수정하거나 DB·파이프라인을 실행하지 않는다.

| 역할 | 시작 입력 | 없어도 진행할 수 있는 일 |
|---|---|---|
| A | 저장소 `s_stock`·Gold 2개, B API·C 가이드 | 실제 컬럼·단위·결측을 반영한 화면과 합성 API fixture |
| B | 저장소 DDL·Silver·Gold·Meta·적재 코드, C 계약 | 제공 CSV 저장·조회·API, Silver/Gold Delta 준비 |
| C | 저장소 Silver·Gold·사전·프로파일·검증·계산 코드 | 실제 전량 분석·신규 Gold 계산·차트 예시 |

Bronze 입력 원본 18개·별도 MySQL 덤프·공시 원문 ZIP·실제 Delta는 포함되지 않았다. 최초 오염 원본 진단·Bronze 재현·전체 원본 대사에 필요한 자료만 구체적으로 요청한다. Silver 전체를 다시 요청하지 않는다. 합성 결과와 실제 데이터 결과를 구분한다.

## 병렬 진행 순서

1. B가 API·실행 계약 초안을, C가 지표·입출력·예외 계약 초안을 제시한다.
2. A는 합성 응답으로 화면을 개발하고, B는 Delta·MySQL·API, C는 검증·Gold 계산을 진행한다.
3. G01~G04의 계약을 맞춘 뒤 실제 데이터를 연결한다.
4. G05 사례 하나를 세 사람이 공통으로 사용해 원본 → Gold → MySQL → API → 화면 값을 대조한다.

API·계산 규칙이 아직 없다는 이유로 다른 역할의 작업 전체를 멈추지 않는다. 임시 계약은 `제안` 상태로 표시하고 실제 계약 확정 전 연동 완료로 체크하지 않는다.

## 실행 상태

현재 실제 인계 데이터·기존 처리 코드·문서·역할 프롬프트·읽기 전용 무결성 검사 명령이 있다. 신규 서비스 실행 명령·lockfile·Docker 환경은 아직 없다. B01에서 실제 환경과 명령을 만들고 검증한 뒤 여기와 README에 등록한다. 고정 인계본의 기존 파이프라인은 외부 입력·DB를 요구하고 출력도 덮어쓰므로 그대로 실행하지 않는다.

## 문서 지도

- [Bronze·Silver·Gold 보완 업무 M01~M14](docs/missing-work.md)

- [최종 목표·레이어·Gold 설계](docs/project-plan.md)
- [실제 데이터·Bronze/Silver 사용 안내](docs/data-guide.md) · [전체 컬럼 사전](docs/data-catalog.md)
- [A01~C12 / G01~G05 / F01~F08 체크리스트](docs/workbook.md)
- [공유 계약과 인수인계 양식](contracts/README.md)
- [A 프롬프트](prompts/A_frontend.md) · [B 프롬프트](prompts/B_backend.md) · [C 프롬프트](prompts/C_analysis.md)

OriginProof는 역할별 시작 프롬프트·담당 경로·계약·검증 구조만 참고했다. 그 프로젝트의 코드·도메인·환경·역할은 적용하지 않는다.
