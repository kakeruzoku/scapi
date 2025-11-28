# -- Path setup --------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("..")) 

# -- Project information -----------------------------------------------------
project = 'Scapi'
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
    'sphinx.ext.intersphinx'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'ja'

autodoc_member_order = 'bysource'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

locale_dirs = ['locales/']

gettext_compact = False

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

from enum import Enum

def skip_enum_members(app, what, name, obj, skip, options):
    # Enum クラスのメンバーをスキップする
    if isinstance(obj, Enum) and obj.__doc__ is not None:
        return True  # 出力しない
    return None  # それ以外はデフォルトの動作に任せる

def setup(app):
    app.connect("autodoc-skip-member", skip_enum_members)

rst_epilog = """
.. _oldwiki: https://kakeruzoku.github.io/scapi
"""

def _make_rst_epilog(name:str,type:str="class",place:str|None=None):
    global rst_epilog
    place = place or name
    rst_epilog += f"\n.. |{name}| replace:: :{type}:`{name} <scapi.{place}>`"

_make_rst_epilog("Session")
_make_rst_epilog("User")
_make_rst_epilog("Project")
_make_rst_epilog("Studio")
_make_rst_epilog("Comment")
_make_rst_epilog("HTTPClient")
_make_rst_epilog("ForumPost")
_make_rst_epilog("ForumCategory")
_make_rst_epilog("ForumTopic")
_make_rst_epilog("Response")
_make_rst_epilog("UNKNOWN","const")