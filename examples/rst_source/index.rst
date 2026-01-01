.. White Paper Title documentation master file

====================================
White Paper Title
====================================

.. rubric:: An Example Technical Document

:Author: Author Name
:Organization: Organization
:Email: author@example.com
:Date: 2025-11-23

.. raw:: latex

   \chapter*{Abstract}
   \addcontentsline{toc}{chapter}{Abstract}

This is an example abstract for the white paper. It provides a brief overview
of the document's contents, methodology, and key findings. The abstract should
be concise yet informative, typically 150-250 words.

This document demonstrates the use of Pandoc for professional technical writing
with automated figure and table generation using Python scripts.

한글도 완벽하게 지원됩니다! Korean text is fully supported!

**Keywords:** technical writing, pandoc, markdown, automation, multilingual

.. raw:: latex

   \tableofcontents
   \clearpage

.. toctree::
   :maxdepth: 3
   :numbered:
   :hidden:

   chapters/01-introduction
   chapters/02-methodology
   chapters/03-results
   chapters/04-conclusion
   chapters/05-korean-example
   chapters/06-system-overview
   chapters/90-appendix-documentation


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
