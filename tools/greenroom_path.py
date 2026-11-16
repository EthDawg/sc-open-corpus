"""Where Green Room lives: $GREEN_ROOM, else a green-room or sc-proving-ground folder beside this repository or in
~/Developer. Its virtualenv python is <app>/.venv/bin/python."""
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CANDIDATES = [os.environ.get('GREEN_ROOM', ''), os.path.join(os.path.dirname(_HERE), 'green-room'),
               os.path.expanduser('~/Developer/green-room'), os.path.join(os.path.dirname(_HERE), 'sc-proving-ground'),
               os.path.expanduser('~/Developer/sc-proving-ground')]
APP = next((p for p in _CANDIDATES if p and os.path.isdir(os.path.join(p, 'greenroom'))), _CANDIDATES[2])
PY = os.path.join(APP, '.venv', 'bin', 'python')
