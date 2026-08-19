import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

from app.services.simulation.service import run_scenario_workflow

payload = {
    'duration': 300,
    'traffic_multiplier': 1.0,
    'intervention_id': 'extend_green_5s_signal_timing'
}

print("Running 1...")
res1 = run_scenario_workflow(payload)
print("Running 2...")
res2 = run_scenario_workflow(payload)

print('Run 1 scenario metrics:')
print(res1['scenario'])
print('Run 2 scenario metrics:')
print(res2['scenario'])
print('Equal?', res1['scenario'] == res2['scenario'])
