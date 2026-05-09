# 드론 재난 대응 시스템 — Claude 작업 가이드

미니어처 프로토타입 데모를 목표로 하는 재난 모니터링 시스템. **공모전 출품작**이라 사실적 임팩트 우선.
라즈베리파이(드론 측) ↔ Windows 메인서버(관제) 양쪽에서 **모노레포로 작업**, GitHub `Minsu059/drone`로 동기화.

## 사용자 프로필

- **한국어로 대화**. 짧고 직접적인 응답 선호. 진행 속도 빠른 편.
- **메인 설계자/개발자** — 서버, 통신, 위험도/경로 모델, 대시보드 담당.
- **담당 아님**: Edge AI 분류 모델(별도 팀원이 학습 중, 미인계), 카메라 모듈(미배송).
  → "Edge AI 직접 만들자"는 제안 금지. 대신 mock 인터페이스로 우회.

## 환경

| 위치 | 경로 | 도구 | 담당 |
|-----|-----|-----|-----|
| 라즈베리파이 | `~/drone/` | Linux ARM64, venv `~/drone/drone/`, `pi@dronepi.local` | edge/, OSM GraphML 캐시 보유 |
| 메인서버 | `C:\drone\` | Windows PowerShell, `.venv\`, FastAPI :8000 + Vite :5173 | server/, dashboard |

**메인서버 git 주의**: 한글 사용자명 `김민수`로 인해 Git for Windows 내장 SSH가 깨짐. 이미 `git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"` 로 강제 설정됨.

## 디렉토리

```
docs/                        설계 문서 (project, A2_Architecture, dashboard, .svg)
server/                      메인서버 작업
├── main.py                  FastAPI 앱 (드론 데이터 수신 + 대시보드 라우트)
├── database.py / models.py  SQLite + Pydantic
├── miniature_map.py         **광역 + 미니어처 데이터 SSOT** (대시보드 fetch 대상)
├── scripts/                 OSM/VWorld/공공데이터 수집·필터
└── dashboard/               Vite + React 19 + TS + react-leaflet 프론트엔드
    ├── src/
    │   ├── App.tsx
    │   ├── api/dashboard.ts          fetch wrapper
    │   ├── components/               WideView, MiniatureView, MiniatureModal, DisasterSidebar
    │   ├── utils/                    risk, mapIcons, coords
    │   └── data/mockData.ts          타입 정의만 (데이터는 백엔드 fetch)
    └── vite.config.ts                dev proxy /api → :8000
edge/                        라즈베리파이 작업 (A2 완료)
├── camera/{base,mock}.py
├── classifier/{base,mock}.py
├── pipeline/{gps,sender,trigger,loop}.py
└── fixtures/manifest.json   9개 시나리오 라벨
data/, cache/, .venv/, drone/   gitignore
```

## 핵심 결정 사항

- **대시보드 SSOT**: 백엔드. `GET /api/dashboard/wide` + `GET /api/dashboard/miniature`. 프론트엔드는 데이터 상수 보유 안 함.
- **프론트 스택**: Vite + React 19 + TS + react-leaflet + lucide-react.
- **미니어처 뷰**: SVG 캔버스 (Leaflet 아님). GPS bbox → viewBox 자동 매핑.
- **위험도 산정**: 인명·붕괴율·화재·도로 4항목 × 25점 = 0~100. `server/dashboard/src/utils/risk.ts` 가 정본.
- **광역 시연 범위**: 한국항공대 반경 5km. 운정/파주 제거됨.
- **광역 도로망**: OSM (osmnx) + GraphML 캐싱. 차단/정체는 좌표 기반 오버레이.
- **행정구역 / 위성타일**: VWorld API (한국 공간정보 오픈플랫폼).
- **공공 인프라**: 대피소/소방서/병원 (공공데이터포털, 반경 10km 필터).
- **2단계 뷰**: 광역 → 한국항공대 구역 클릭 → 미니어처 풀스크린 모달.
- **Edge AI 분류 스키마는 flat**: `fire_detected` + `fire_confidence` (nested 아님).
- **트랙 분리**: A(본인, mock으로 끝까지) / B(Edge AI/카메라 외부 의존) / C(통합).
- **라이선스 표기 의무**: 푸터에 OSM, VWorld, 공공데이터 출처 명시.

상세는 `docs/project.md` 의 "결정 사항 / TBD" 섹션 참조.

## 진행 상태 (2026-05-09 기준, 상세는 `git log`)

- [x] git 모노레포 + GitHub SSH 동기화 (양쪽 환경, 한글 사용자명 우회 포함)
- [x] 메인서버 server/ 코드 통합 (database, main, models, miniature_map)
- [x] OSM 도로망 캐싱 (라즈베리파이 `data/road_kau_5km.graphml`, 6773 노드 / 18503 엣지)
- [x] 데이터 수집 스크립트 3종 + README 작성 (`server/scripts/`)
- [x] Edge AI 인터페이스 flat 통일
- [x] **A2 edge pipeline 완료** — ABC + Mock + 9 fixture + Pipeline + 메인서버 통합 검증 (5 disaster_report 송수신 OK)
- [x] **대시보드 Phase 1~3 완료** — Vite/React 골격 → 광역 정교화(위험도/사이드바/아이콘) → 백엔드 라우트 통합

**다음 우선순위 (병렬 가능)**:
- VWorld 인증키 발급 후 `download_vworld_boundary.py` 실행 → 행정구역 GeoJSON
- 공공데이터 CSV 3개 (대피소/소방서/병원) 다운로드 → `filter_public_data.py` 실행
- 메인서버 venv에 osmnx 설치 + GraphML 받기 (라즈베리파이 SCP 또는 새로 다운로드)
- 대시보드에 OSM 도로 그래프 통합 (광역 진입 경로 표시)
- 위험도 추론 모델 백엔드 통합 (현재 risk.ts는 프론트 계산 — 백엔드로 이전 검토)
- 경로 추론 엔진 (NetworkX A*/Dijkstra + 차단/정체 가중치)
- A2 fixture 이미지 채우기 (AI Hub / Mendeley 발췌 또는 미니어처 촬영)

## 작업 시작 루틴

1. **`git pull` 먼저** (반대편 환경 변경분 받기).
2. 작업 영역에 맞춰 읽기:
   - 대시보드 → `docs/dashboard.md` + `server/dashboard/README.md` + `server/miniature_map.py`
   - Edge AI mock / 카메라 → `docs/A2_Architecture.md`
   - 외부 데이터 수집 → `server/scripts/README.md`
   - 전체 그림 / 결정 / TBD → `docs/project.md`
3. 기존 코드 스타일 존중 (FastAPI 라우트 패턴, SQLite, Pydantic 모델, React 컴포넌트 분리 방식).
4. 작업 끝나면 `git add` / `commit` / `push`. **작은 단위 commit 권장** — 양쪽 환경 충돌 최소화.

## 동기화 흐름 (양쪽 동시 작업 시)

```
git add <파일>
git commit -m "..."
git push
# push 거부되면 (반대편이 그 사이에 push한 경우):
git pull --rebase
git push
```

같은 파일을 양쪽에서 다르게 수정한 경우 conflict 마커 발생 → 수동 머지 후 `git rebase --continue`.

## 외부 데이터 / 데모 좌표

- **시연 장소**: 한국항공대학교 (`37.6000, 126.8645`)
- **광역 반경**: 5km (OSM), 6km (VWorld 행정구역), 10km (공공 인프라)
- **미니어처 좌표 매핑**: 실물 1m ↔ GPS 80m (`local_to_gps()` — `docs/dashboard.md` 좌표 매핑 정책 참조)
- **가상 재난 5건 (광역)**: 행신동 가스누출, 화전동 침수, 능곡역 붕괴, 향동 화재, 행주산성 산사태
- **드론**: 가상 4대 (drone-v1~v4) + 실제 1대 (drone-01, 라즈베리파이 송신)

## 주의

- **Edge AI 모델 직접 학습 금지** — 외부 팀원 담당. mock 분류기로 진행.
- **카메라 의존 작업 금지** — `CameraSource` 추상화로 우회. 카메라 도착 후 `PiCameraSource` 교체 예정.
- **commit 시**: 시스템 자동 hooks 외에는 `--no-verify` 등 우회 금지. 한국어 메시지 OK.
- **데모 시 인터넷 의존 최소화**: OSM/VWorld 모두 다운로드 1회 후 로컬 파일로 운영.
- **데이터 SSOT 일관성**: 광역/미니어처 데이터는 `server/miniature_map.py` 기준. 프론트는 `/api/dashboard/*` fetch만.
