"""
End-to-end API test for Sentinel-GNN
"""
import requests
import json

print('\n' + '='*70)
print('TESTING FULL API END-TO-END')
print('='*70 + '\n')

payload = {
    'isolate_id': 'Escherichia coli',
    'patient_profile': {
        'Age': 65,
        'Gender': 'Male',
        'Diabetes': True,
        'Hospital_before': True,
        'Hypertension': True,
        'Infection_Freq': 4
    }
}

print('Sending request to http://localhost:8000/api/analyze...\n')
print('Payload:')
print(json.dumps(payload, indent=2))
print()

try:
    response = requests.post('http://localhost:8000/api/analyze', json=payload)
    
    if response.status_code == 200:
        print('✓ API Response: SUCCESS (200)\n')
        result = response.json()
        
        print('Response Summary:')
        print(f'  • Isolate: {result["isolate_id"]}')
        print(f'  • Prediction: {result["ml_prediction"]["prediction"]}')
        print(f'  • Confidence: {result["ml_prediction"]["confidence"]:.2%}')
        print(f'  • Risk Factors: {result["ml_prediction"]["risk_factors"]}')
        strategy_text = result['strategy'][:80] + '...' if len(result['strategy']) > 80 else result['strategy']
        print(f'  • Strategy: {strategy_text}')
        print(f'  • Trace Steps: {len(result["trace"])}')
        for i, step in enumerate(result['trace'], 1):
            step_text = step[:70] + '...' if len(step) > 70 else step
            print(f'    {i}. {step_text}')
    else:
        print(f'✗ API Response: ERROR ({response.status_code})')
        print(f'  {response.text}')
        
except Exception as e:
    print(f'✗ Request failed: {e}')
    print('  (Is the backend running on port 8000?)')

print()
