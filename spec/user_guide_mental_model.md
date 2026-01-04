# Understanding the Documentation System: A Guide for Authors and Analysts

이 가이드는 이 문서 시스템이 **왜** 이렇게 설계되었는지, 그리고 어떻게 사용해야 하는지 설명합니다.

---

## 해결하려는 문제

인캐빈 모니터링 시스템 평가 파이프라인은 다음과 같이 동작합니다:

```
테스트 데이터셋 → DMS S/W → Raw JSON → 분석 스크립트 → 성능 Metrics
```

이 결과물로 **세 가지 문서**가 필요합니다:

| 문서 | 용도 | 갱신 주기 (예상) | 내용 범위 |
|------|------|-----------|-----------|
| 내부 성능 분석 보고서 | 개발자/이해관계자용 | 주 1회 | 모든 수치, 수십 개의 table/figure |
| 외부 KPI 보고서 | 협력사 전달용 | 월 1회 이하 | SDK API 기능 성능만 |
| Dossier | 인증기관 제출용 | 필요시 | 안전성 관련 기능만 |

### 기존 방식의 문제점

**Copy-paste 방식**:
- 분석 노트북에서 숫자를 복사해서 Word에 붙여넣기
- S/W가 업데이트될 때마다 수동으로 숫자 갱신
- 내부 보고서와 외부 보고서의 숫자가 다른 경우 발생
- "어떤 버전이 맞는 숫자인가?" 혼란

**별도 문서 관리 방식**:
- 내부용, 외부용, Dossier용 파일을 각각 관리
- 같은 내용을 세 군데서 수정
- 버전 관리가 어려움

### 이 시스템의 해결책

**하나의 소스에서 세 가지 문서 생성**:

```
분석 스크립트
    ↓
Artifacts (JSON tables, figures) + Registry
    ↓
원고 (.md/.rst) ← 최소한의 설명 글만 작성
    ↓
Build Pipeline
    ↓
├── 내부 보고서 (모든 내용)
├── 외부 KPI 보고서 (external 이상만)
└── Dossier (dossier만)
```

- 수치는 분석 스크립트가 생성
- 설명 문장은 한 번만 작성
- visibility 태그로 어떤 문서에 포함될지 결정
- 빌드할 때마다 최신 수치로 자동 갱신

---

## 핵심 개념: 문서는 컴파일되는 프로그램

이 시스템의 핵심 아이디어는 **문서를 소스 코드처럼 취급**하는 것입니다:

| 프로그래밍 개념 | 문서 시스템 |
|----------------|-------------|
| 소스 코드 | `.md` / `.rst` 원고 파일 |
| 라이브러리 | 분석 결과 Artifacts (JSON, PNG) |
| 심볼 테이블 | Registry (ID → 메타데이터) |
| 컴파일러 | Normalization + Resolution 파이프라인 |
| linking | placeholder를 실제 테이블/그림으로 교체 |
| 실행 파일 | 렌더링된 PDF/HTML |

**왜 이렇게 하는가?**

- **수치가 중요합니다.** 수치는 기계적으로 생성되며, 사람이 수정할 이유가 없습니다.
- **라이브러리를 업데이트하면 재컴파일하듯이**, 분석 결과가 바뀌면 문서를 다시 빌드합니다.
- **컴파일 에러가 나면 수정해야 하듯이**, 빌드 실패는 허용하지 않습니다.

---

## 작성자(Author)가 알아야 할 것

### 당신의 역할: 방향을 제안하고 추적성을 생성한다. 자세한 내용은 시스템이 채운다

원고에서 당신이 할 일은 **무엇이 들어갈지 선언**하는 것이지, **실제 데이터를 넣는 것이 아닙니다**.

```markdown
<!-- BEGIN tbl.face.yaw_mae.v1 -->
Yaw 각도별 MAE(Mean Absolute Error)를 보여주는 테이블입니다.
극단적인 각도(±60° 이상)에서 오차가 증가하는 것은 self-occlusion 때문입니다.
<!-- END tbl.face.yaw_mae.v1 -->
```

당신이 한 것:
- `tbl.face.yaw_mae.v1`이라는 테이블이 여기 들어간다고 선언
- 테이블을 설명하는 설명문 작성

시스템이 하는 것:
- Registry에서 이 ID의 메타데이터 조회
- 해당 artifact 파일(JSON)에서 테이블 데이터 로드
- placeholder를 실제 Pandoc Table로 교체
- 렌더링 시 PDF/HTML 테이블로 변환

### 왜 이렇게 분리하는가?

**숫자가 바뀌어도 설명문의 구조는 그대로입니다.**

DMS S/W가 업데이트되어 Yaw MAE가 3.2°에서 2.8°로 개선되었다면:
1. 분석 스크립트를 다시 돌립니다
2. 새 artifact가 생성됩니다
3. 문서를 다시 빌드합니다
4. 테이블에 새 숫자가 들어갑니다
5. **설명문을 직접 수정할 필요 없음** (여전히 "Yaw 각도별 MAE"를 설명함)

### 절대 하지 말아야 할 것

❌ **Computed block 안에 실제 데이터를 쓰지 마세요**

```markdown
<!-- 잘못된 예시 -->
<!-- BEGIN tbl.face.yaw_mae.v1 -->
| Yaw Angle | MAE (°) |
|-----------|---------|
| -60°      | 4.2     |
| 0°        | 2.1     |
| +60°      | 4.5     |
<!-- END tbl.face.yaw_mae.v1 -->
```

이 테이블은 빌드 시 artifact 데이터로 **완전히 교체**됩니다.

❌ **노트북에서 숫자를 복사해서 본문에 넣지 마세요**

```markdown
<!-- 잘못된 예시 -->
전체 평균 MAE는 2.8°입니다.
```

이 숫자는 다음 빌드에서 artifact가 업데이트되어도 그대로입니다. Metric block을 사용하세요:

```markdown
<!-- 올바른 예시 -->
전체 평균 MAE는 아래와 같습니다.

<!-- BEGIN metric.face.yaw_mae_overall.v1 -->
<!-- END metric.face.yaw_mae_overall.v1 -->
```

---

## 분석 담당자(Analyst)가 알아야 할 것

### 당신의 역할: Artifact를 생성하고 Registry에 등록

분석 스크립트의 출력물:

1. **Artifact 파일**: 테이블 JSON, figure 이미지, metric JSON
2. **Registry 항목**: 각 artifact의 메타데이터

```python
# 분석 스크립트 예시
def generate_yaw_mae_table(test_results):
    df = compute_mae_by_yaw_angle(test_results)

    # Artifact 저장
    artifact = {
        "columns": [
            {"key": "yaw_angle", "label": "Yaw Angle", "dtype": "str"},
            {"key": "mae", "label": "MAE (°)", "dtype": "float", "unit": "°"}
        ],
        "rows": df.to_dict('records')
    }
    save_json(artifact, "artifacts/tables/yaw_mae.json")

    # Registry 항목 반환
    return {
        "tbl.face.yaw_mae.v1": {
            "role": "computed",
            "kind": "table",
            "source": "artifacts/tables/yaw_mae.json",
            "schema": "table.simple.json@v1",
            "visibility": "external"  # 외부 KPI 보고서에도 포함
        }
    }
```

### Semantic ID가 중요한 이유

Semantic ID는 분석 코드와 문서 사이의 **안정적인 계약**입니다.

**좋은 ID**: `tbl.face.yaw_mae.by_angle.v1`
- 무엇인지 알 수 있음 (table, face 인지 기능, yaw MAE)
- 버전이 있음 (v1)
- 구조가 바뀌면 버전을 올림

**나쁜 ID**: `table_3`, `result_final`
- 의미를 알 수 없음
- 순서가 바뀌면 혼란
- 버전 관리 불가

### Visibility 설정

세 문서에 무엇이 포함될지는 `visibility` 필드로 결정합니다:

```json
{
  "tbl.face.debug.raw_predictions.v1": {
    "visibility": "internal"    // 내부 보고서에만
  },
  "tbl.face.yaw_mae.v1": {
    "visibility": "external"    // 내부 + 외부 KPI
  },
  "tbl.face.safety_kpi.v1": {
    "visibility": "dossier"     // 내부 + 외부 + Dossier
  }
}
```

**Monotonic Condensation 원칙**:
```
Internal ⊇ External ⊇ Dossier
```

- Dossier에 있는 모든 것은 External에도 있음
- External에 있는 모든 것은 Internal에도 있음
- 반대는 성립하지 않음

이 원칙 덕분에 **실수로 내부 데이터가 외부로 유출되는 것을 방지**합니다.

### Artifact는 결정론적이어야 함

같은 입력 → 같은 출력. 이를 위해:

- **타임스탬프 넣지 않기**: `"generated_at": "2024-01-15"` 같은 필드 제거
- **정렬 순서 고정**: `df.sort_values(['yaw_angle']).reset_index(drop=True)`
- **부동소수점 포맷 고정**: `round(value, 4)` 일관되게 사용

왜? 시스템이 artifact를 diff해서 변경 여부를 감지합니다. 비결정론적 출력은 가짜 변경을 만들어 혼란을 줍니다.

---

## Visibility 모델: 왜 세 단계인가?

### Internal: 모든 것

내부 성능 분석 보고서에 들어가는 내용:
- 디버그용 중간 결과
- 실험적 분석
- 코드 스니펫
- 내부 링크

`visibility: "internal"`로 설정된 모든 것이 포함됩니다.

### External: 협력사 공유 가능

외부 KPI 보고서에 들어가는 내용:
- SDK API 기능의 성능
- 공식 metric
- 테스트셋 특성 설명

`visibility: "external"` 또는 `"dossier"`가 포함됩니다.

### Dossier: 인증 제출용

인증 기관 제출용 Dossier에 들어가는 내용:
- 안전성 관련 기능의 성능만
- 검증된 수치만
- 재현 가능한 결과만

`visibility: "dossier"`만 포함됩니다.

### 왜 이렇게 설계했는가?

**하나의 원고에서 세 문서를 생성**하려면, 각 블록이 "어디까지 공개할 것인가"를 알아야 합니다.

세 레벨이 **포함 관계**인 이유:
- Dossier에 들어가는 내용이 외부 KPI 보고서에 없으면 이상함
- 외부에 공개한 내용을 내부에서 모르면 안 됨
- **가장 제한적인 문서는 항상 덜 제한적인 문서의 부분집합**

이 설계 덕분에 visibility 필터 하나로 세 문서를 일관되게 생성할 수 있습니다.

---

## 버전 관리: `.v1`을 `.v2`로 올릴 때

Semantic ID에는 버전 접미사가 있습니다: `tbl.face.yaw_mae.v1`

### 버전을 올려야 할 때

- **컬럼 추가/삭제**: 테이블 구조가 바뀜
- **의미 변경**: 같은 이름이지만 계산 방식이 달라짐
- **단위 변경**: 퍼센트에서 소수로, 도(°)에서 라디안으로

### 버전을 올리지 않아도 될 때

- **값 업데이트**: 새 데이터, 같은 구조
- **포맷 변경**: 소수점 자릿수 변경
- **설명 수정**: 테이블 주변 설명 변경

### 왜 버전이 필요한가?

버전이 없다면:
1. 분석 스크립트가 테이블에 컬럼을 추가함
2. 빌드가 성공함
3. 하지만 설명에는 "두 컬럼 테이블"이라고 써 있음
4. 아무도 모르고 배포됨

버전이 있다면:
1. 분석 스크립트가 `tbl.face.yaw_mae.v2`로 버전 올림
2. 문서에는 아직 `v1`을 참조
3. 빌드 실패: "v1을 찾을 수 없음"
4. 작성자가 설명을 검토하고 v2에 맞게 수정

---

## Annotation: 해석 추가하기

테이블이나 그림에 **해석**을 붙이고 싶을 때 annotation을 사용합니다.

```markdown
<!-- BEGIN tbl.face.yaw_mae.v1 -->
Yaw 각도별 MAE 테이블입니다.
<!-- END tbl.face.yaw_mae.v1 -->

<!-- BEGIN tbl.face.yaw_mae.v1.annotation -->
**해석**: ±60° 이상에서 오차가 급격히 증가하는 것은 자기 가림 때문입니다.
이는 DMS의 설계 범위(±45°) 내에서는 문제가 되지 않습니다.
타겟 유즈케이스는 전면 주시이므로 수용 가능한 수준입니다.
<!-- END tbl.face.yaw_mae.v1.annotation -->
```

### 왜 Annotation을 별도 블록으로?

Annotation은 **바인딩된 computed block과 생명 주기를 같이 합니다**:

- `tbl.face.yaw_mae.v1`이 외부 문서에서 제거되면, annotation도 자동 제거
- Annotation의 visibility는 바인딩된 테이블을 따름
- 테이블 없이 해석만 남는 상황 방지

### Inline Prose vs Annotation

**Inline Prose** (computed block 안):
```markdown
<!-- BEGIN tbl.face.yaw_mae.v1 -->
Yaw 각도별 MAE 테이블입니다.  ← 캡션 역할, 짧게
<!-- END tbl.face.yaw_mae.v1 -->
```

**Annotation** (별도 블록):
```markdown
<!-- BEGIN tbl.face.yaw_mae.v1.annotation -->
**해석**: 상세한 분석과 맥락 설명...  ← 해석, 길어도 됨
<!-- END tbl.face.yaw_mae.v1.annotation -->
```

---

## 자주 하는 실수와 해결법

### 실수: Computed 내용을 직접 수정

**증상**: PDF에서 숫자를 수정했는데 다음 빌드에서 원래대로 돌아감

**원인**: Computed block은 매 빌드마다 artifact에서 재생성됨

**해결**: 분석 스크립트를 수정하고 artifact를 재생성

### 실수: 세 문서에서 숫자가 다름

**증상**: 내부 보고서와 외부 보고서의 MAE 값이 다름

**원인**: 다른 소스에서 복사했거나, 다른 시점의 artifact 사용

**해결**: 모든 문서가 같은 semantic ID를 참조하도록 확인

### 실수: Registry에 항목 누락

**증상**: 빌드 실패 - "unknown semantic ID"

**원인**: 문서에 ID를 추가했지만 registry에는 안 넣음

**해결**: 분석 스크립트에서 해당 artifact와 registry 항목 생성

### 실수: 버전 안 올림

**증상**: 빌드는 성공하지만 설명과 테이블이 안 맞음

**원인**: 테이블 구조를 바꿨지만 같은 ID 사용

**해결**: 구조가 바뀌면 `.v1` → `.v2`로 버전 필요. 버전 관리를 수동으로 하지 말 것. 분석 스크립트 에서 자동으로 처리.

---

## 빌드 프로세스: 무엇이 일어나는가

```
1. Parse      : .md/.rst → Pandoc AST
2. Normalize  : Semantic block 식별, Registry에서 메타데이터 주입
3. Resolve    : placeholder → 실제 artifact 내용으로 교체
4. Validate   : 계약 검증 (ID 유일성, visibility 규칙, 타입 체크)
5. Filter     : Build target에 따라 내용 필터링
6. Render     : PDF / HTML / Markdown으로 출력
```

각 단계에서 문제가 있으면 **빌드가 실패**합니다. 이것은 의도된 동작입니다.

### 왜 엄격하게?

- **조용히 틀린 문서가 생기는 것 보다 빌드 실패가 낫습니다.** 사람이 리뷰하는 노력 조차 최대한 줄이기 위함입니다.
- 내부 데이터가 외부로 유출되는 것을 방지합니다.
- 오래된 수치가 남아있는 것을 방지합니다.
- 깨진 참조가 있는 문서 배포를 방지합니다.

---

## Python 네이티브인 이유

기존 도구들의 문제:

| 도구 | 문제점 |
|------|--------|
| Quarto | Lua 필터 필요. Python에서 디버깅 불가. pandas 직접 사용 불가. |
| MyST | JavaScript 생태계. Node.js 런타임 필요. |
| Typst | 자체 스크립팅 언어. torch/pandas import 불가. |

이 시스템의 장점:

- **pytest로 문서 변환 로직 테스트**
- **기존 Python 테스트 파이프라인에 통합**
- **Internal/External/Dossier 자동화 외에, 추가 커스텀 빌드 타겟 구현 가능**

```python
# 분석 코드와 문서 생성이 같은 언어
def test_yaw_mae_artifact_generation():
    results = load_test_results("run_2024_01_15")
    artifact = generate_yaw_mae_table(results)

    assert "columns" in artifact
    assert len(artifact["rows"]) > 0
    assert all(row["mae"] >= 0 for row in artifact["rows"])
```

---

## 요약: 세 가지 원칙

1. **이름을 붙이고, 시스템이 채운다**
   - Semantic ID로 무엇이 들어갈지 선언
   - 실제 데이터는 artifact에서 옴

2. **소스는 저장소, 출력물은 컴파일 결과**
   - `.md`/`.rst` 파일과 분석 스크립트가 진실
   - PDF/HTML은 빌드 결과물

3. **Visibility는 항상 정해져야함**
   - 시스템이 보장: internal 내용은 external에 안 나감
   - 실수로 유출 불가능

---

## Quick Reference

### 작성자용

| 작업 | 방법 |
|------|------|
| 테이블 추가 | `<!-- BEGIN tbl.your.id.v1 -->` ... `<!-- END -->` |
| 그림 추가 | `<!-- BEGIN fig.your.id.v1 -->` ... `<!-- END -->` |
| Metric 추가 | `<!-- BEGIN metric.your.id.v1 -->` ... `<!-- END -->` |
| 해석 추가 | `<!-- BEGIN tbl.your.id.v1.annotation -->` ... `<!-- END -->` |

### 분석 담당자용

| 작업 | 방법 |
|------|------|
| Artifact 정의 | Registry에 `role`, `kind`, `source`, `schema` 추가 |
| Visibility 설정 | `visibility` 필드: `"internal"`, `"external"`, `"dossier"` |
| 구조 변경 | 버전 올림 (`.v1` → `.v2`), Registry 업데이트 |

---

## 관련 문서

- **[authoring_conventions.md](authoring_conventions.md)** — Markdown/RST 문법 상세
- **[architecture.md](architecture.md)** — 시스템 아키텍처
- **[error_codes.md](error_codes.md)** — 에러 메시지 해석과 해결법
- **[initial_concept.md](initial_concept.md)** — 프로젝트 시작 배경
