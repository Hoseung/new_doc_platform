.. _`sec:korean`:

===============================
한글 사용 예제 / Korean Example
===============================

이 장에서는 한글과 영어를 함께 사용하는 방법을 보여줍니다.

This chapter demonstrates how to use Korean and English together in your white paper.

.. _`sec:mixed`:

혼합 언어 작성 / Mixed Language Writing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

기본 텍스트 / Basic Text
^^^^^^^^^^^^^^^^^^^^^^^^

한글과 영어를 자연스럽게 섞어서 사용할 수 있습니다. You can naturally mix Korean and English text. 예를 들어, **머신러닝** (machine learning)이나 **딥러닝** (deep learning)과 같은 기술 용어를 함께 사용할 수 있습니다.

기술 문서에서는 종종 한글 설명과 영어 원어를 병기합니다:

- **인공지능** (Artificial Intelligence, AI)
- **자연어 처리** (Natural Language Processing, NLP)
- **컴퓨터 비전** (Computer Vision, CV)

수식과 한글 / Equations with Korean
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

한글 설명과 함께 수학 공식을 사용할 수 있습니다. Mathematical equations can be used with Korean explanations.

정규분포의 확률밀도함수는 다음과 같이 정의됩니다:

.. math:: f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}

\ {#eq:korean-normal}

여기서 :math:`\mu`\ 는 평균 (mean), :math:`\sigma`\ 는 표준편차 (standard deviation)입니다.

.. _`sec:korean-tables`:

표와 그림 / Tables and Figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

한글 표 / Korean Tables
^^^^^^^^^^^^^^^^^^^^^^^

한글로 작성된 표의 예시입니다. Here is an example of a table with Korean text:

.. table:: 온도에 따른 실험 결과 / Experimental results by temperature
   :name: tbl:korean-experiment

   +-----------+-----------+------------+----------+------------+-------------+-------+
   | 실험 번호 | 온도 (°C) | 압력 (kPa) | 수율 (%) | Experiment | Temperature | Yield |
   +===========+===========+============+==========+============+=============+=======+
   | 실험-1    | 20.5      | 101.3      | 78.3     | Exp-1      | 20.5°C      | 78.3% |
   +-----------+-----------+------------+----------+------------+-------------+-------+
   | 실험-2    | 25.0      | 105.2      | 82.1     | Exp-2      | 25.0°C      | 82.1% |
   +-----------+-----------+------------+----------+------------+-------------+-------+
   | 실험-3    | 30.5      | 110.1      | 85.7     | Exp-3      | 30.5°C      | 85.7% |
   +-----------+-----------+------------+----------+------------+-------------+-------+
   | 실험-4    | 35.0      | 115.8      | 89.2     | Exp-4      | 35.0°C      | 89.2% |
   +-----------+-----------+------------+----------+------------+-------------+-------+
   | 실험-5    | 40.5      | 121.3      | 92.5     | Exp-5      | 40.5°C      | 92.5% |
   +-----------+-----------+------------+----------+------------+-------------+-------+

표 @tbl:korean-exp 에서 볼 수 있듯이, 온도가 증가함에 따라 수율도 함께 증가했습니다.

As shown in Table @tbl:korean-exp, the yield increased with temperature.

방법론 비교 표 / Method Comparison Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. table:: 다양한 방법론의 성능 비교 / Performance comparison of different methods
   :name: tbl:korean-methods

   ====== ========== ========= =========== ======
   방법   정확도 (%) 속도 (ms) 메모리 (MB) 복잡도
   ====== ========== ========= =========== ======
   방법 A 92.5       12.3      256         낮음
   방법 B 94.3       15.7      512         중간
   방법 C 91.8       10.2      128         낮음
   방법 D 95.1       18.4      1024        높음
   ====== ========== ========= =========== ======

.. _`sec:korean-refs`:

교차 참조 / Cross-References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

섹션 참조 / Section References
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

한글로 된 섹션도 쉽게 참조할 수 있습니다. Korean sections can be easily referenced.

- 서론은 Section @sec:introduction 을 참조하세요
- 방법론은 Section @sec:methodology 를 참조하세요
- 이 장의 표 섹션은 Section @sec:korean-tables 에 있습니다

그림 참조 / Figure References
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

영어 장의 그림도 참조할 수 있습니다:

- Figure @fig:example_plot 는 삼각함수 그래프를 보여줍니다
- Figure @fig:scatter 는 산점도와 회귀선을 보여줍니다
- Figure @fig:heatmap 은 상관관계 히트맵입니다

수식 참조 / Equation References
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Equation @eq:korean-normal 은 정규분포를 나타내며, Equation @eq:gaussian 은 같은 공식의 영어 버전입니다.

.. _`sec:korean-citations`:

인용 / Citations
~~~~~~~~~~~~~~~~

한글로 작성할 때도 인용을 동일하게 사용할 수 있습니다. Citations work the same way in Korean text.

최근 연구에 따르면 [@example2024], 자동화된 문서 작성 시스템이 재현성을 크게 향상시킨다고 합니다.

여러 문헌을 동시에 인용할 수도 있습니다 [@example2024; @examplebook2023].

.. _`sec:korean-code`:

코드 블록 / Code Blocks
~~~~~~~~~~~~~~~~~~~~~~~

한글 주석이 포함된 코드 예제:

.. prose::
   :id: code:korean-example

   .. code:: python

      # 한글 주석도 잘 표시됩니다
      import numpy as np
      import matplotlib.pyplot as plt

      # 데이터 생성
      x = np.linspace(0, 10, 100)
      y = np.sin(x)

      # 그래프 그리기
      plt.plot(x, y)
      plt.xlabel('시간 (초)')  # X축 레이블
      plt.ylabel('진폭')       # Y축 레이블
      plt.title('사인파 그래프')
      plt.show()

.. _`sec:korean-lists`:

목록 / Lists
~~~~~~~~~~~~

순서 있는 목록 / Ordered List
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

연구 진행 단계:

1. **문헌 조사** (Literature Review)

   - 관련 연구 검색
   - 선행 연구 분석

2. **실험 설계** (Experimental Design)

   - 변수 선정
   - 측정 방법 결정

3. **데이터 수집** (Data Collection)

   - 실험 수행
   - 결과 기록

4. **분석 및 해석** (Analysis and Interpretation)

   - 통계 분석
   - 결과 해석

순서 없는 목록 / Unordered List
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

주요 기여사항:

- **재현성 향상**: 모든 그림과 표를 자동으로 생성
- **다국어 지원**: 한글, 영어, 일본어, 중국어 등 지원
- **버전 관리**: Git을 통한 효율적인 협업
- **다양한 출력 형식**: PDF, HTML, DOCX 등

.. _`sec:korean-formatting`:

강조와 서식 / Emphasis and Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

한글에서도 다양한 서식을 사용할 수 있습니다:

- **굵게** (bold)
- *기울임* (italic)
- [STRIKEOUT:취소선] (strikethrough)
- ``코드`` (inline code)
- `링크 <https://example.com>`__ (link)

.. _`sec:korean-findings`:

주요 결과 / Key Findings
~~~~~~~~~~~~~~~~~~~~~~~~

이 예제 장에서 다룬 내용:

1. **혼합 언어 작성**: 한글과 영어를 자연스럽게 섞어 사용
2. **표와 그림**: 한글 레이블과 캡션 사용 (Tables @tbl:korean-exp, @tbl:korean-methods)
3. **수식**: 한글 설명과 함께 수학 공식 사용 (Equation @eq:korean-normal)
4. **교차 참조**: 한글 텍스트에서 섹션, 그림, 표 참조
5. **코드**: 한글 주석이 포함된 코드 블록
6. **서식**: 다양한 마크다운 서식 기능

.. _`sec:korean-conclusion`:

결론 / Conclusion
~~~~~~~~~~~~~~~~~

Pandoc과 XeLaTeX를 사용하면 한글과 영어를 완벽하게 혼용할 수 있습니다. Using Pandoc with XeLaTeX enables perfect mixing of Korean and English.

한글 폰트가 제대로 설치되어 있다면, 별도의 추가 설정 없이도 한글 문서를 작성할 수 있습니다. With proper Korean fonts installed, you can write Korean documents without additional configuration.

더 자세한 정보는 `KOREAN_SUPPORT.md <../KOREAN_SUPPORT.md>`__ 문서를 참조하세요. For more information, see the `KOREAN_SUPPORT.md <../KOREAN_SUPPORT.md>`__ guide.
