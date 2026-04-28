import os
import sys
from datetime import datetime

# Add project root so Sphinx can import `bhpy`
sys.path.insert(0, os.path.abspath('..'))

project = 'bhpy'
author = 'Becker & Hickl'
copyright = f"{datetime.now().year}, {author}"

# Try to get version from installed/adjacent package
try:
    import bhpy as _bh
    release = getattr(_bh, '__version__', '') or '3.3.0'
except Exception:
    release = '3.3.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# Avoid import errors for optional/heavy deps at doc build time
autodoc_mock_imports = [
    'Crypto',
    'zeroconf',
    'appdirs',
    'numpy',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_theme_options = {'logo_only': True}
html_static_path = ['_static']
html_logo = '_static/BHPython.svg'
html_favicon = '_static/BHPython.svg'
html_css_files = [
    'custom.css',
]
