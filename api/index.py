import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import create_app

app = create_app('production')

# Vercel expects a callable named `app`
