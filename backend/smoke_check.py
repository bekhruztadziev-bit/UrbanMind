import os
import sys

os.chdir(r'C:\Users\user\UrbanMind')
os.environ['SUMO_HOME'] = r'C:\Users\user\Downloads\sumo-win64-1.27.1\sumo-1.27.1'
sys.path.insert(0, r'C:\Users\user\UrbanMind\backend')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print('health=', client.get('/api/health').json())
print('metrics=', client.post('/api/metrics', json={'steps': 30}).json())
opt = client.post('/api/optimize', json={'steps': 30}).json()
print('best_candidate=', opt['best_candidate']['id'])
print('ai=', opt['ai']['recommendation'])
print('mahalla=', client.get('/api/mahalla').json()['name'])
