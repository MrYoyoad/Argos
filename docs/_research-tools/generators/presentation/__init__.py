"""
Presentation package — modular PPTX generator for Argos VSP.

Submodules:
    config           — paths, colors, layout constants
    helpers          — slide setup, text, shapes, animations, reusable builders
    slides_opening   — Sections 0-2: Opening, Context, The Problem
    slides_research  — Sections 3-5: Research Findings, Understanding Why, Tuning
    slides_evaluation— Section 6 + Salvage + Demos
    slides_engineering — Section 7: Engineering
    slides_future    — Section 8: Future Directions + Appendix
"""

from .config import *       # noqa: F401,F403
from .helpers import *      # noqa: F401,F403
from .slides_opening import *       # noqa: F401,F403
from .slides_research import *      # noqa: F401,F403
from .slides_evaluation import *    # noqa: F401,F403
from .slides_engineering import *   # noqa: F401,F403
from .slides_future import *        # noqa: F401,F403
