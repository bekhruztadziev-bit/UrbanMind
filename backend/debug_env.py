import os
import sys
print('SUMO_HOME=', os.environ.get('SUMO_HOME'))
print('PYTHONPATH=', os.environ.get('PYTHONPATH'))
print('python_exe=', sys.executable)
try:
    import traci
    print('traci_ok')
except Exception as exc:
    print('traci_missing', exc)
try:
    import app.main
    print('app_main_ok')
except Exception as exc:
    print('app_main_missing', exc)
