from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_metrics_and_transaction_flow():
    m=client.get('/api/metrics').json(); assert m['n_test']>0 and 0<=m['roc_auc']<=1
    r=client.post('/api/investigate',json={'amount':45000,'hour':2,'customer_age_days':1,'transactions_24h':9,'failed_attempts_24h':3,'distance_km':1200,'device_trust':.1,'is_international':True,'is_new_device':True,'payment_method':'card'})
    assert r.status_code==200 and r.json()['investigation']['risk_score']>=0
