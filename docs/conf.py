# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
project = 'scapi'
copyright = '2024, かける族'
author = 'かける族'

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scapi', 'utils', 'common.py')
with open(_path, 'r', encoding='utf-8') as fp:
    init = fp.read()

release = init.replace(" ","").split("__version__=\"")[1].split("\"")[0]


# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
]

source_encoding = 'utf-8-sig'

source_suffix = '.rst'

master_doc = 'index'

language = 'ja'

exclude_patterns = []

pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'


# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
}


# -- Extension configuration -------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': False,
    'show-inheritance': True,
}

todo_include_todos = True