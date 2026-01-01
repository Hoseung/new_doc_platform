========================================
reStructuredText Syntax Reference Guide
========================================

:Author: Sphinx Documentation System
:Date: 2025-11-30
:Version: 1.0

.. contents:: Table of Contents
   :depth: 3
   :local:

Introduction
============

reStructuredText (reST) is a lightweight markup language designed for technical documentation. It is the default markup language for Sphinx documentation and Python documentation.

This guide covers the essential syntax for writing reStructuredText documents.

Basic Formatting
================

Paragraphs
----------

Paragraphs are blocks of text separated by blank lines. Line breaks within a paragraph are ignored.

Example::

    This is a paragraph.
    This is still the same paragraph.

    This is a new paragraph.

Inline Markup
-------------

**Bold text**
    Use double asterisks: ``**bold text**``

*Italic text*
    Use single asterisks: ``*italic text*``

``Code/literal text``
    Use double backticks: ````code text````

:subscript:`subscript`
    Use ``:subscript:`text```

:superscript:`superscript`
    Use ``:superscript:`text```

Headers and Sections
====================

Section headers are created by underlining (and optionally overlining) text with punctuation characters. The hierarchy is determined by the order they appear.

Common convention::

    ######################
    Part (overline + underline)
    ######################

    ************************
    Chapter (overline + underline)
    ************************

    Section
    =======

    Subsection
    ----------

    Subsubsection
    ^^^^^^^^^^^^^

    Paragraph
    """""""""

Lists
=====

Bullet Lists
------------

Use ``*``, ``+``, or ``-`` for bullet points::

    * Item 1
    * Item 2

      * Nested item 2.1
      * Nested item 2.2

    * Item 3

Enumerated Lists
----------------

Use numbers or letters::

    1. First item
    2. Second item
    3. Third item

Or automatic numbering::

    #. First item
    #. Second item
    #. Third item

Definition Lists
----------------

::

    term
        Definition of the term.

    another term
        Definition of another term.
        Can have multiple paragraphs.

Code Blocks
===========

Literal Code Blocks
-------------------

Use double colons ``::`` followed by indented text::

    This is a paragraph ending with double colon::

        def hello_world():
            print("Hello, World!")

Code Blocks with Syntax Highlighting
-------------------------------------

Use the ``.. code-block::`` directive:

.. code-block:: python

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

Syntax::

    .. code-block:: python

        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

Supported languages include: ``python``, ``c``, ``cpp``, ``java``, ``javascript``, ``bash``, ``sql``, and many more.

Links and References
====================

External Links
--------------

Inline link::

    `Python <https://www.python.org/>`_

Separated link reference::

    See the `Python website`_ for more information.

    .. _Python website: https://www.python.org/

Internal Cross-References
--------------------------

Create a label::

    .. _my-reference-label:

    Section to Cross-Reference
    ===========================

Reference it::

    See :ref:`my-reference-label` for details.

Document Links
--------------

Link to another document::

    :doc:`other_document`
    :doc:`Path to document </path/to/document>`

Images and Figures
==================

Images
------

.. image:: https://via.placeholder.com/150
   :alt: Alternative text
   :width: 150px

Syntax::

    .. image:: path/to/image.png
       :alt: Alternative text
       :width: 80%
       :align: center

Figures
-------

Figures are images with captions:

.. figure:: https://via.placeholder.com/200
   :alt: Figure alternative text
   :width: 200px
   :align: center

   This is the figure caption.

Syntax::

    .. figure:: path/to/image.png
       :alt: Figure alternative text
       :width: 80%
       :align: center

       This is the figure caption.

Tables
======

Simple Tables
-------------

::

    =====  =====  =======
      A      B    A and B
    =====  =====  =======
    False  False  False
    True   False  False
    False  True   False
    True   True   True
    =====  =====  =======

Grid Tables
-----------

::

    +------------------------+------------+----------+----------+
    | Header row, column 1   | Header 2   | Header 3 | Header 4 |
    +========================+============+==========+==========+
    | body row 1, column 1   | column 2   | column 3 | column 4 |
    +------------------------+------------+----------+----------+
    | body row 2             | ...        | ...      |          |
    +------------------------+------------+----------+----------+

List Tables
-----------

.. list-table:: Table Caption
   :header-rows: 1
   :widths: 20 30 50

   * - Header 1
     - Header 2
     - Header 3
   * - Row 1, Col 1
     - Row 1, Col 2
     - Row 1, Col 3
   * - Row 2, Col 1
     - Row 2, Col 2
     - Row 2, Col 3

CSV Tables
----------

.. csv-table:: CSV Table Example
   :header: "Name", "Age", "City"
   :widths: 30, 10, 30

   "Alice", 30, "New York"
   "Bob", 25, "San Francisco"
   "Charlie", 35, "Seattle"

Mathematics
===========

Inline Math
-----------

Use the ``:math:`` role for inline equations: :math:`E = mc^2`

Syntax::

    The famous equation :math:`E = mc^2` was discovered by Einstein.

Block Math
----------

Use the ``.. math::`` directive for display equations:

.. math::

   \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}

With labels for referencing:

.. math::
   :label: gaussian

   f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}

Reference it: :eq:`gaussian`

Syntax::

    .. math::
       :label: gaussian

       f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}

    Reference the equation: :eq:`gaussian`

Admonitions
===========

Admonitions are specially formatted blocks for notes, warnings, etc.

Note
----

.. note::

   This is a note admonition.

Warning
-------

.. warning::

   This is a warning admonition.

Important
---------

.. important::

   This is an important admonition.

Tip
---

.. tip::

   This is a tip admonition.

Caution
-------

.. caution::

   This is a caution admonition.

Danger
------

.. danger::

   This is a danger admonition.

Custom Admonition
-----------------

.. admonition:: Custom Title

   This is a custom admonition with a custom title.

Syntax::

    .. note::

       This is a note admonition.

    .. admonition:: Custom Title

       This is a custom admonition.

Directives
==========

Contents/Table of Contents
--------------------------

::

    .. contents:: Table of Contents
       :depth: 2
       :local:

Include Other Files
-------------------

::

    .. include:: other_file.rst

Literal Include (Code Files)
-----------------------------

::

    .. literalinclude:: example.py
       :language: python
       :lines: 1-10
       :emphasize-lines: 3,5

Sidebar
-------

.. sidebar:: Sidebar Title

   This is sidebar content that appears to the side of the main text.

Topic
-----

.. topic:: Topic Title

   This is a topic block.

Comments
========

Comments are not rendered in the output::

    .. This is a comment
       It can span multiple lines
       As long as they are indented

    ..
       Another way to write
       multi-line comments

Line Blocks
===========

Preserve line breaks using ``|``::

    | Line 1
    | Line 2
    |     Indented line 3
    | Line 4

Result:

| Line 1
| Line 2
|     Indented line 3
| Line 4

Footnotes and Citations
=======================

Footnotes
---------

Auto-numbered footnote [#]_ and another [#]_.

Named footnote [#note]_.

.. [#] This is the first footnote.
.. [#] This is the second footnote.
.. [#note] This is a named footnote.

Citations
---------

Citation reference [CIT2002]_.

.. [CIT2002] Citation text goes here.

Syntax::

    Auto-numbered footnote [#]_ and another [#]_.

    .. [#] This is the first footnote.
    .. [#] This is the second footnote.

    Citation reference [CIT2002]_.

    .. [CIT2002] Citation text goes here.

Substitutions
=============

Define a substitution::

    .. |name| replace:: replacement text

    .. |longtext| replace:: This is a very long text that
       can be referenced multiple times without retyping it.

Use it: |name| and |longtext|

Special substitutions::

    |today|     - Current date
    |version|   - Project version

Raw HTML/LaTeX
==============

For HTML Output
---------------

::

    .. raw:: html

       <div style="color: red;">
           This is red text in HTML output.
       </div>

For LaTeX/PDF Output
--------------------

::

    .. raw:: latex

       \begin{center}
       \textbf{Centered bold text in LaTeX}
       \end{center}

Sphinx-Specific Features
========================

Code Documentation
------------------

::

    .. automodule:: mymodule
       :members:

    .. autoclass:: MyClass
       :members:

    .. autofunction:: my_function

Index and Glossary
------------------

Create index entries::

    .. index::
       single: Python
       pair: programming; language

Glossary::

    .. glossary::

       term1
          Definition of term1.

       term2
          Definition of term2.

Cross-References in Sphinx
---------------------------

Reference to sections::

    :ref:`label-name`

Reference to documents::

    :doc:`document-name`

Reference to Python objects::

    :func:`function_name`
    :class:`ClassName`
    :mod:`module_name`
    :meth:`Class.method`

Download Links
--------------

::

    :download:`Download this file <path/to/file.pdf>`

Best Practices
==============

1. **Consistent Header Style**

   Use a consistent hierarchy of section markers throughout your document.

2. **Meaningful Labels**

   Use descriptive labels for cross-references::

       .. _intro-section:

   Instead of::

       .. _sec1:

3. **Proper Indentation**

   Directives and their content must be properly indented (usually 3 spaces).

4. **Blank Lines**

   Use blank lines to separate elements clearly.

5. **Code Block Languages**

   Always specify the language for syntax highlighting::

       .. code-block:: python

6. **Image Paths**

   Use relative paths from the source directory::

       .. image:: ../images/figure.png

7. **Table Captions**

   Use ``:name:`` option for table references::

       .. list-table:: Caption
          :name: table-label

8. **Math Equations**

   Use ``:label:`` for equations you want to reference::

       .. math::
          :label: eq-name

Quick Reference Card
====================

==================  ====================================
Syntax              Result
==================  ====================================
``**bold**``        **bold**
``*italic*``        *italic*
````code````        ``code``
``:sub:`text```     :subscript:`text`
``:sup:`text```     :superscript:`text`
``link_``           Hyperlink
``:ref:`label```    Cross-reference
``:doc:`name```     Document link
``:math:`x^2```     :math:`x^2`
``.. image::``      Image
``.. figure::``     Figure with caption
``.. code-block::`` Code with highlighting
``.. note::``       Note admonition
``.. math::``       Display equation
==================  ====================================

Resources
=========

Official Documentation
----------------------

* `reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
* `Sphinx Documentation <https://www.sphinx-doc.org/>`_
* `Docutils reST Spec <https://docutils.sourceforge.io/rst.html>`_

Tools and Editors
-----------------

* **Sphinx** - Documentation generator
* **Visual Studio Code** - With reST extensions
* **PyCharm** - Built-in reST support
* **Online Editor** - `rst.ninjs.org <http://rst.ninjs.org/>`_

Conclusion
==========

reStructuredText is a powerful markup language for technical documentation. Its clear syntax and extensive features make it ideal for:

- Software documentation
- Technical reports
- Academic papers
- API documentation
- Books and tutorials

With Sphinx, reST becomes even more powerful, enabling automatic API documentation, cross-referencing across multiple documents, and multiple output formats (HTML, PDF, ePub, etc.).

.. note::

   This guide covers the most common reST syntax. For advanced features and edge cases, consult the official Sphinx and Docutils documentation.
