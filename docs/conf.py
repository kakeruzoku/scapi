# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
project = 'Scapi'
copyright = '2024, かける族'
author = 'かける族'

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scapi', 'utils', 'common.py')
with open(_path, 'r', encoding='utf-8') as fp:
    init = fp.read()

release = init.replace(" ","").split("__version__=\"")[1].split("\"")[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'ja'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
}

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': False,
    'show-inheritance': True,
}

todo_include_todos = True