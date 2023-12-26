# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import django


# This is a fix for the following exception when converting rst to pdf
# NotImplementedError: None:None the 'desc_sig_space' node is not yet supported (rinoh.frontend.sphinx.nodes)
from rinoh.frontend.rst import DocutilsInlineNode


class Desc_Sig_Space(DocutilsInlineNode):
    pass


sys.path.insert(0, os.path.abspath(".."))
os.environ["DJANGO_SETTINGS_MODULE"] = "vzs.settings"
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "VZS Členská sekce"
copyright = "2023, Peter Fačko, Jakub Levý, Vojtěch Švandelík"
author = "Peter Fačko, Jakub Levý, Vojtěch Švandelík"
language = "cs"

# Rinoh configuration
rinoh_documents = [
    dict(
        doc="index",
        target="vzs-clenska-sekce",
        title="VZS Členská sekce",
        subtitle="Dokumentace",
        template="article",
    )
]


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
