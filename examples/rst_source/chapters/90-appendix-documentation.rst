.. _`sec:appendix`:

Appendix: Project Documentation
===============================

This appendix contains comprehensive documentation for the Pandoc white paper authoring system.

.. _`sec:quickstart`:

A. Quick Start Guide
--------------------

Installation (Linux)
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # System dependencies
   sudo apt update
   sudo apt install pandoc texlive-full fonts-noto-cjk build-essential

   # Python environment
   curl -LsSf https://astral.sh/uv/install.sh | sh
   cd pandoc_report
   uv venv
   source .venv/bin/activate
   uv pip install matplotlib numpy pandas seaborn scipy pillow tabulate pyyaml

Daily Workflow
~~~~~~~~~~~~~~

.. code:: bash

   # 1. Activate environment
   source .venv/bin/activate

   # 2. Generate content
   python scripts/generate_figures.py
   python scripts/generate_tables_v2.py

   # 3. Build document
   make pdf              # or: make html, make all

Common Commands
~~~~~~~~~~~~~~~

============== =================================
Command        Description
============== =================================
``make all``   Generate figures, tables, and PDF
``make pdf``   Build PDF only
``make html``  Build HTML only
``make clean`` Remove generated documents
``make help``  Show all available commands
============== =================================

.. _`sec:build-guide`:

B. Build System Guide
---------------------

Makefile vs Shell Script
~~~~~~~~~~~~~~~~~~~~~~~~

**Use ``make pdf`` (Recommended):** - Simpler commands - Automatic dependency handling - Includes pandoc-crossref filter - Industry standard

**Use ``./build_example.sh`` (For learning):** - Shows exact Pandoc commands - Useful for debugging - Educational purposes

Build Process
~~~~~~~~~~~~~

::

   1. make figures  →  2. make tables  →  3. make preprocess  →  4. Pandoc build
      (Python)            (Python)           (Replace {{table:..}})    (PDF/HTML)

.. _`sec:korean-support`:

C. Korean/CJK Language Support
------------------------------

Setup
~~~~~

.. code:: bash

   # Install Korean fonts
   sudo apt install fonts-noto-cjk fonts-noto-cjk-extra

   # Fonts are pre-configured in metadata.yaml:
   # CJKmainfont: "Noto Serif CJK KR"

Usage
~~~~~

Simply write Korean in your markdown:

.. code:: markdown

   # 서론 {#sec:intro}

   한글과 English를 자유롭게 섞어 사용할 수 있습니다.

   {{table:tbl:05-korean-data}}

Korean in Matplotlib
~~~~~~~~~~~~~~~~~~~~

.. code:: python

   from utils.korean_plot import setup_korean_font
   setup_korean_font()

   plt.xlabel('한글 레이블')
   plt.ylabel('값')

.. _`sec:automatic-tables`:

D. Automatic Table System
-------------------------

Table Format (Self-Contained Objects)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each table is a ``.md`` file with YAML frontmatter:

.. code:: yaml

   ---
   id: tbl:03-results
   caption: "Experimental results"
   description: "Detailed context about the table"
   chapter: 3
   tags: [experimental, temperature]
   ---

   | Column 1 | Column 2 |
   |----------|----------|
   | Data     | Data     |

Creating Tables
~~~~~~~~~~~~~~~

.. code:: python

   from table_manager import TableManager

   tm = TableManager(chapter=3)
   tm.save_table(
       data,
       name="my-results",
       caption="Experimental results",
       description="Results from temperature experiments",
       tags=["experimental"]
   )
   # Saves to: ../_static/tables/chapter-03/table-my-results.md

Using Tables in Chapters
~~~~~~~~~~~~~~~~~~~~~~~~

**Placeholder syntax:**

.. code:: markdown

   ## Results

   We conducted experiments:

   {{table:tbl:03-my-results}}

   The results show...

**Modes:** - ``{{table:tbl:03-name}}`` - Full mode (includes description) - ``{{table:tbl:03-name|inline}}`` - Inline mode (table only)

.. _build-process-1:

Build Process
~~~~~~~~~~~~~

.. code:: bash

   make pdf  # Automatically replaces placeholders!

The preprocessor: 1. Scans chapters for ``{{table:...}}`` placeholders 2. Loads tables from ``../_static/tables/`` 3. Replaces placeholders with actual content 4. Builds document

Manual Preprocessing
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # Preview changes
   python scripts/table_preprocessor.py --dry-run

   # Replace placeholders
   python scripts/table_preprocessor.py

   # List available tables
   python scripts/table_preprocessor.py --list-tables

.. _`sec:paths`:

E. Path Configuration
---------------------

Path Rules
~~~~~~~~~~

All paths in markdown files are **relative to project root**:

::

   pandoc_report/              ← Run `make pdf` here
   ├── chapters/
   │   └── 03-results.md       ← Your file
   ├── ../_static/
   │   ├── figures/
   │   │   └── plot.png        → ../_static/figures/plot.png
   │   └── tables/
   │       └── chapter-03/     → {{table:tbl:03-name}}
   └── assets/
       └── images/
           └── logo.png         → assets/images/logo.png

Correct Paths
~~~~~~~~~~~~~

.. code:: markdown

   <!-- ✅ CORRECT -->
   ![Plot](../_static/figures/example_plot.png){#fig:plot}
   ![Logo](assets/images/logo.png)
   {{table:tbl:03-results}}

   <!-- ❌ WRONG -->
   ![Plot](../../_static/figures/example_plot.png)

Fixing Path Issues
~~~~~~~~~~~~~~~~~~

.. code:: bash

   # Fix all image paths
   find chapters/ -name "*.md" -exec sed -i 's|../../_static/|../_static/|g' {} \;

.. _`sec:troubleshooting`:

F. Troubleshooting
------------------

Common Issues
~~~~~~~~~~~~~

**Makefile: “source: not found”** - Fixed! Makefile now uses bash shell directly - Python called via ``.venv/bin/python``

**Images not found** - Check paths are from project root: ``../_static/figures/plot.png`` - Not relative to chapter: ``../../_static/figures/plot.png``

**Korean text shows as boxes**

.. code:: bash

   sudo apt install fonts-noto-cjk
   fc-cache -fv

**Table placeholder not replaced**

.. code:: bash

   # List available tables
   python scripts/table_preprocessor.py --list-tables

   # Check placeholder syntax
   {{table:tbl:03-name}}  # ✅ Correct
   {{tbl:03-name}}        # ❌ Wrong

**pandoc-crossref version warning** - Minor warning, usually safe to ignore - Cross-references still work - Update pandoc-crossref to match Pandoc version if needed - See: https://github.com/lierdakil/pandoc-crossref/releases

**Python ModuleNotFoundError**

.. code:: bash

   source .venv/bin/activate
   uv pip install matplotlib numpy pandas seaborn scipy pillow tabulate pyyaml

.. _`sec:architecture`:

G. Project Architecture
-----------------------

Directory Structure
~~~~~~~~~~~~~~~~~~~

::

   pandoc_report/
   ├── chapters/              # Markdown chapter files
   │   ├── 01-introduction.md
   │   ├── 02-methodology.md
   │   ├── 03-results.md
   │   └── 90-appendix-documentation.md
   ├── scripts/              # Python scripts
   │   ├── generate_figures.py
   │   ├── generate_tables_v2.py
   │   ├── table_manager.py
   │   ├── table_preprocessor.py
   │   └── utils/
   │       └── korean_plot.py
   ├── ../_static/               # Generated content
   │   ├── figures/
   │   └── tables/
   │       └── chapter-{NN}/
   ├── assets/               # Static resources
   │   └── images/
   ├── templates/            # Pandoc templates
   ├── references/           # Bibliography
   │   └── references.bib
   ├── metadata.yaml         # Document metadata
   ├── Makefile             # Build automation
   ├── pyproject.toml       # Python dependencies
   └── README.md            # Quick start guide

File Organization
~~~~~~~~~~~~~~~~~

**Source files (commit to git):** - ``chapters/*.md`` - Your content - ``scripts/*.py`` - Analysis and generation - ``metadata.yaml`` - Document configuration - ``Makefile`` - Build system - ``pyproject.toml`` - Dependencies

**Generated files (don’t commit):** - ``../_static/figures/*.png`` - Generated plots - ``../_static/tables/**/*.md`` - Generated tables - ``*.pdf``, ``*.html`` - Build outputs - ``.venv/`` - Virtual environment

.. _`sec:advanced`:

H. Advanced Features
--------------------

Cross-References
~~~~~~~~~~~~~~~~

.. code:: markdown

   # Chapter {#sec:chapter}

   ## Results {#sec:results}

   ![Plot](../_static/figures/plot.png){#fig:plot width=80%}

   | A | B |
   |---|---|
   | 1 | 2 |

   : Caption {#tbl:data}

   $$E = mc^2$$ {#eq:einstein}

   See Section @sec:results, Figure @fig:plot,
   Table @tbl:data, and Equation @eq:einstein.

Citations
~~~~~~~~~

.. code:: markdown

   Recent work [@smith2020; @jones2021] shows...
   @smith2020 demonstrated that...

Add entries to ``references/references.bib``:

.. code:: bibtex

   @article{smith2020,
     title={Example Article},
     author={Smith, John},
     journal={Example Journal},
     year={2020}
   }

Custom Pandoc Options
~~~~~~~~~~~~~~~~~~~~~

Edit ``Makefile`` to add options:

.. code:: makefile

   COMMON_OPTS = --number-sections --toc --toc-depth=3 \
                 --highlight-style=tango \
                 --variable=geometry:margin=1in

Multiple Output Formats
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   make pdf          # PDF via LaTeX
   make html         # Standalone HTML
   make docx         # Microsoft Word
   make all-formats  # All formats

.. _`sec:best-practices`:

I. Best Practices
-----------------

1. Version Control
~~~~~~~~~~~~~~~~~~

.. code:: gitignore

   # Commit source files
   chapters/
   scripts/
   metadata.yaml
   Makefile
   pyproject.toml

   # Don't commit generated files
   ../_static/
   *.pdf
   *.html
   .venv/

2. Table Management
~~~~~~~~~~~~~~~~~~~

- Use descriptive names: ``table-temperature-results.md``
- Include descriptions for context
- Tag tables for organization
- Regenerate when data changes

3. Figure Quality
~~~~~~~~~~~~~~~~~

.. code:: python

   # Save at high DPI for publication
   plt.savefig('../_static/figures/plot.png', dpi=300, bbox_inches='tight')

4. Modular Chapters
~~~~~~~~~~~~~~~~~~~

- One chapter per file
- Use meaningful section IDs
- Keep chapters focused

5. Reproducibility
~~~~~~~~~~~~~~~~~~

.. code:: bash

   # Document your workflow
   make clean-all    # Remove everything
   make all          # Rebuild from scratch

.. _`sec:reference`:

J. Quick Reference
------------------

Build Commands
~~~~~~~~~~~~~~

.. code:: bash

   make pdf          # Build PDF
   make html         # Build HTML
   make all          # Everything
   make clean        # Remove outputs
   make help         # Show options

Python Scripts
~~~~~~~~~~~~~~

.. code:: bash

   # Generate content
   python scripts/generate_figures.py
   python scripts/generate_tables_v2.py
   python scripts/my_analysis.py

   # Manage tables
   python scripts/table_preprocessor.py --list-tables
   python scripts/table_preprocessor.py --dry-run

Markdown Syntax
~~~~~~~~~~~~~~~

.. code:: markdown

   # Heading {#sec:id}
   ![Caption](path){#fig:id width=80%}
   : Caption {#tbl:id}
   $$equation$$ {#eq:id}
   {{table:tbl:03-name}}
   [@citation]
   @fig:id, @tbl:id, @sec:id

File Paths
~~~~~~~~~~

============= =============================
Resource      Path Format
============= =============================
Figures       ``../_static/figures/name.png``
Tables        ``{{table:tbl:NN-name}}``
Static images ``assets/images/name.png``
Bibliography  ``references/references.bib``
============= =============================

.. _`sec:resources`:

K. Resources
------------

Documentation
~~~~~~~~~~~~~

- Pandoc Manual: https://pandoc.org/MANUAL.html
- Pandoc-Crossref: https://lierdakil.github.io/pandoc-crossref/
- Markdown Guide: https://www.markdownguide.org/
- UV: https://github.com/astral-sh/uv
- Matplotlib: https://matplotlib.org/

Project Files
~~~~~~~~~~~~~

- ``scripts/table_manager.py`` - TableManager API
- ``scripts/table_preprocessor.py`` - Preprocessor
- ``scripts/demo_table_workflow.py`` - Working demo
- ``Makefile`` - Build system reference

Getting Help
~~~~~~~~~~~~

.. code:: bash

   # Show available make targets
   make help

   # List available tables
   python scripts/table_preprocessor.py --list-tables

   # Check versions
   pandoc --version
   python --version
   make --version

.. _`sec:feature-summary`:

L. Summary of Features
----------------------

✅ Implemented Features
~~~~~~~~~~~~~~~~~~~~~~~

1. **Automated Build System**

   - Makefile with dependency management
   - Automatic figure/table generation
   - Multi-format output (PDF, HTML, DOCX)

2. **Korean/CJK Language Support**

   - Full UTF-8 support
   - Korean fonts configured
   - Mixed language documents
   - Korean matplotlib plots

3. **Automatic Table System**

   - Self-contained table objects
   - YAML frontmatter metadata
   - Placeholder replacement
   - Multiple modes (full/inline)

4. **Reproducible Workflow**

   - Python-based generation
   - Version control friendly
   - UV virtual environment
   - Documented dependencies

5. **Professional Output**

   - Publication-quality figures (300 DPI)
   - Automatic numbering
   - Cross-references
   - Bibliography management

6. **Developer-Friendly**

   - Modular architecture
   - Clear documentation
   - Example scripts
   - Troubleshooting guides

This system provides a complete, professional authoring environment for technical white papers with automated content generation and multi-language support.
