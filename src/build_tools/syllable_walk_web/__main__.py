"""Module entrypoint for the Pipe-Works creator workbench.

This stays intentionally tiny so ``python -m build_tools.syllable_walk_web``
behaves exactly like the installed ``pipeworks-namegen-lexicon-web`` script.
"""

import sys

from build_tools.syllable_walk_web.cli import main

sys.exit(main())
