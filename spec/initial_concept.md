1. 문제 정의
1.1 목표
Driver Monitoring System(DMS)의 성능 정보를 제공하는 기술 문서 작성 효율화

DMS 평가는 reproducibility를 위해 이미 정의된 테스트 데이터셋을 DMS S/W에 넣고 raw 결과를 JSON으로 추출한 뒤, JSON을 분석하여 최종 분석 결과를 생성함. 

다양한 인지 기능이 있으며, 그 특성과 성능을 이해하기 위해 다양한 수준과 범위의 데이터 평가가 진행 됨

총 3가지의 문서가 필요함

내부 보고서, 협력사 전달용 KPI 보고서, 인증 기관 제출용 성능 보고서 (Dossier)

원론적으로 한가지 제품의 성능을 표현하는 서로 다른 형식이므로 중복되는 작업을 피할 수 있음

DMS S/W에 minor 업데이트가 있을 때마다 인지기능 정상 작동 여부 확인을 위해 평가 스크립트를 돌릴 수 있음

주 1회 정도의 cadence로 문서가 내부 보고서가 업데이트 될 수 있음

외부 KPI 보고서, Dossier는 월 1회 이하의 cadence 예상

기술문서이므로 최초 작성 이후에 수치 업데이트만 자동으로 이루어질 수 있다고 판단

1.2 요구사항
1.2.1 최종 산출물의 특성
총 3가지의 문서가 필요함

내부 성능 분석 보고서

협력사 전달용 KPI 보고서 

인증 기관 제출용 성능 보고서 (Dossier)

3개의 문서는 서로 다른 용도임.

내부 성능 분석 보고서

개발자 및 이해관계자가 궁금해하는 모든 수치를 제공

수십개의 table과 수십개의 Figure 예상

다양한 resource로의 hyperlink 예상

Note, Callout등의 추가 설명 element 많이 필요

Code snippet 다수 포함

외부 KPI 보고서

SDK의 API에 포함되는 기능의 성능만 포함

미리 정의된 주요 metric 외 추가 분석용 metric 필요 없음

테스트의 정당성을 설명하기 위해 최종 metric 생성에 사용된 테스트 셋의 특성 설명 자료 필요

Dossier

‘안전성’에 직접적으로 관련된 기능의 경험적 성능만 포함 됨

back data는 별도로 제출할 가능성 높음

1.2.2 문제 해결 방향
하나의 실험 결과로 3개의 문서 작성

실험에 대한 기술 공통

주요 성능 metric 공통

내부 성능 분석 보고서 > 외부 KPI 보고서 > Dossier 순으로 condence/filter된 정보

Human intervention 최소화

기술 문서이므로 수치 업데이트 시 작문 작업 최소화

내부 성능 분석 보고서는 CI/CD 파이프라인에 통합되면 좋음

분석 과정 자체에 가장 많은 domain expertise 투입

데이터 분석과 통계

제품에 대한 이해 

결과에 대한 검토

문서 자동 생성 기능 필요

일정 수준 이상의 편집 기능 필요

MS Word처럼 편집 기능의 자율성 필요 없음

---------------------------------
More technical thoughts: Why build a new paltform? 

Your team needs to produce reproducible white papers, maintain product documentation, and generate executive summaries—all from the same source data, without becoming LaTeX operators or web developers. This article explains why we chose a Python-native, AST-first architecture and how it compares to established alternatives.

The Problem: Tooling Mismatch for AI/Product Teams
Existing documentation tools fall into two camps, both ill-suited for AI development workflows:

Monolithic systems (Quarto, Sphinx): Powerful but require learning Lua, YAML schemas, or JavaScript ecosystems foreign to Python data science teams.quarto+1​

Markup-centric tools (Typst, AsciiDoc): Focus on authoring experience but lack programmatic integration with Python-based testing pipelines, pandas dataframes, and ML models.typst+1​

When your test harness generates performance metrics in Python, translating those results into documentation shouldn't require manual copy-pasting or writing Lua filters. The architecture must treat documentation as a software artifact within the Python ecosystem.

Decision 1: Python-Native AST Manipulation (Not Lua or JavaScript)
Our Choice: All document transformations are Python classes operating on a Panflute AST. You can set breakpoints, import pandas, and use pytest on your documentation logic.

Alternative: Quarto's Lua Filters
Quarto uses Pandoc's Lua interpreter for AST transformations. While Lua is lightweight and embeddable, it fractures the development workflow:quarto​

Debugging requires print() statements or external tools

No native pandas, requests, or LLM library access

Context-switching between Python (data) and Lua (presentation) creates cognitive overheadnews.ycombinator+1​

Alternative: MyST's JavaScript Ecosystem
MyST-MD uses a TypeScript AST specification and JavaScript transformers. This fits web-centric teams but forces AI researchers into Node.js tooling, adding a second language runtime to ML pipelines.executablebooks+1​

Alternative: Typst's Integrated Scripting
Typst merges markup with a custom scripting language, achieving elegant self-contained documents. However, its isolation is a liability for product documentation—you cannot import torch or query your test database directly. The language is still maturing, and ecosystem gaps require awkward workarounds.github+1​

Justification for Python-Native:
Your team already maintains Python code for model training, testing, and deployment. Documentation transformers should use the same IDE, debugger, and dependencies. When a transformer fails, pdb drops you into familiar Python code, not Lua stack traces. This reduces maintenance friction and leverages institutional Python expertise.arxiv+1​

Decision 2: Single Source, Multiple Views via AST (Not Preprocessing or Conditional Markup)
Our Choice: Transformers like VisibilityTransformer and LinkSanitizerTransformer operate on the AST to produce audience-specific outputs. The same source document generates an internal engineering spec, a partner white paper, and an executive summary.

Alternative: AsciiDoc Conditionals
AsciiDoc uses preprocessor directives (ifeval, ifdef) to include/exclude content. This works but pollutes source files with audience logic:asciidoc​



text
ifeval::["{audience}" == "internal"] // Internal details here endif::[] 

The logic is string-based and error-prone. Worse, conditionals don't compose—nesting them creates a maintenance nightmare.adoc-studio​

Alternative: Quarto Filter Chains
 Quarto supports Lua filters for content filtering, but the ecosystem is fragmented. Each filter is a separate file with implicit ordering dependencies. There's no standard pattern for "remove internal sections" or "sanitize links"—you write Lua from scratch.quarto+1​

Alternative: Djot's Uniformity Principle
 Djot's syntax standardization reduces parsing ambiguity, but it doesn't address transformation logic. Djot is a markup language, not a publishing pipeline. It provides no built-in mechanism for audience-specific rendering.haskell+1​

Justification for AST-Level Views:
 AST transformations are composable and testable. A VisibilityTransformer class has explicit methods, unit tests, and clear dependencies. When you need to generate an executive summary, you can:

Run the full transformer stack to get the technical report AST

Apply an LLMSummarizerTransformer that calls openai.ChatCompletion to condense sections

Render the summarized AST to PDF

The LLM integration is seamless because the transformer is Python. You can pass dataframes, configuration objects, and even model checkpoints directly to the summarization logic. This is impossible with Lua or AsciiDoc preprocessors.

Decision 3: Composable Transformer Stack (Not Static Configuration)
Our Choice: Transformers are Python classes in a list. The pipeline executes them sequentially, passing the mutated AST between stages. This is explicit code, not YAML magic.

Alternative: Pandoc Filter Ordering
 Pandoc's filter system applies filters in command-line order: pandoc --filter filter1.lua --filter filter2.lua. This is fragile—renaming filters changes behavior, and there's no way to conditionally skip filters based on document metadata.grokipedia+1​

Alternative: Asciidoctor Extensions
 Asciidoctor uses Ruby extensions that hook into parsing events. While powerful, the extension API is callback-based and harder to compose. Extensions can interfere with each other, and debugging requires Ruby knowledge.capgemini.github+1​

Alternative: Docling's Enrichment Pipeline
 Docling uses a linear pipeline: parse → enrich → assemble → export. This matches our architecture but targets document extraction from PDFs, not authoring. The enrichment steps are hardcoded for OCR and table detection, not customizable for business logic.arxiv+1​

Justification for Composable Stack:
 Reproducible documentation requires explicit, versioned transformation logic. When a test result table needs to be regenerated from a new dataset, you want:



python
class TestResultTransformer:     def transform(self, ast, test_run_id):         df = load_test_results(test_run_id)         table_node = self.create_table_from_df(df)         return self.replace_placeholder(ast, table_node) 

This is reviewable, testable Python code committed alongside your documentation. The transformer stack is just a list in a configuration file, making it obvious what runs when. For reproducibility, you pin the transformer versions and test run IDs in git.

Decision 4: AST-Centric Static Sites (Not HTML Templates)
Our Choice: Site navigation is generated as an AST (nested Link nodes) and composed with content into a single tree. The same VisibilityTransformer that hides internal paragraphs also removes internal pages from the sidebar.

Alternative: Quarto's HTML Templates
 Quarto uses Pandoc's template system for site layout. The navigation is often rendered separately from content, creating a "dumb HTML template" problem. If a filter removes a page from the AST, the template's navigation logic may still link to it, causing 404s.quarto-tdg+1​

Alternative: Jupyter Book 2 Component System
 Jupyter Book 2 uses MyST's component system, where React components render the site structure. This is AST-aware but ties you to the JavaScript ecosystem. The build process involves webpack, npm, and JSX—far from Python data pipelines.mystmd-react-bug.readthedocs+1​

Justification for AST Composition:
 For product documentation, business logic must apply consistently across content and navigation. Consider a "Secret Feature" available to beta customers:

The feature's .md page is marked {.internal}

The navigation link in _toc.yml is also marked {.internal}

A single VisibilityTransformer removes both nodes from the AST

With HTML templates, you'd need two separate mechanisms: a filter for content and custom template logic for navigation. AST composition ensures the "single source of truth" for visibility rules. When LLMs generate documentation variants, they operate on one coherent tree, not fragmented HTML snippets.

The LLM Integration Strategy
Our architecture is designed for LLM-augmented documentation. With documents as Python AST objects:

Content Generation: An LLMTransformer can call GPT-4 to draft sections based on test results, then parse the markdown output into AST nodes and insert them into the tree.

Audience Adaptation: The same transformer can condense technical sections for executives or expand acronyms for partners, all while preserving document structure.

Validation: Post-LLM, a LinkValidatorTransformer can use requests to verify that generated links actually work.

This is impractical in Lua (no LLM libraries) and cumbersome in JavaScript (async/await in build pipelines). Python's openai package and synchronous style fit naturally.

Conclusion: The Right Tool for Python/Product Teams
LitePub is not architecturally novel—it synthesizes proven ideas from Pandoc, Quarto, and Docling. Its value is ecosystem alignment:

Quarto is ideal for R/statistics teams comfortable with Luaquarto+1​

MyST excels for scholarly publishing in JavaScript environmentsmystmd+1​

Typst is perfect for self-contained documents without external datatypst+1​

AsciiDoc suits enterprises with Ruby infrastructureasciidoc+1​

Docling focuses on extracting structure from existing documentsarxiv+1​

LitePub is for Python/AI product teams who:

Generate documentation from test results and dataframes

Need LLM integration for content adaptation

Want to debug documentation logic like application code

Prefer composition over configuration

The architecture trades some maturity for ecosystem fit. We're not replacing Pandoc's renderer or inventing a new markup language. We're providing the programmable middleware that makes Pandoc's power accessible to Python teams, with debuggability and LLM integration as first-class concerns.