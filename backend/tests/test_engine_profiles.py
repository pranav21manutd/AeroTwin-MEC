"""Run from backend: python -m unittest discover -s tests -v."""
import copy
import logging
import unittest
import warnings

import yaml
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.engine_profile_store import engine_profiles, EngineProfile, profile_alerts
from main import app

logging.disable(logging.WARNING)

class EngineProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_catalog_and_exact_yaml(self):
        catalog = self.client.get('/api/engine/profiles').json()
        self.assertEqual(len(catalog['profiles']), 5)
        for profile in catalog['profiles']:
            with self.subTest(engine=profile['engine_id']):
                response = self.client.get(f"/api/engine/profile/{profile['engine_id']}/yaml")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.text, engine_profiles.raw_yaml(profile['engine_id']))
                loaded = yaml.safe_load(response.text)
                self.assertEqual(loaded['engine_id'], profile['engine_id'])
                self.assertEqual(len(loaded['sensor_map']), 8)
                self.assertTrue(all(file['available'] for file in profile['files']))

    def test_unknown_and_malformed_selection_do_not_mutate(self):
        before = engine_profiles.active()
        for body in ({'engine_id': '../../main'}, {'engine_id': 'missing'}):
            self.assertEqual(self.client.post('/api/engine/select', json=body).status_code, 404)
        self.assertEqual(self.client.post('/api/engine/select', json={}).status_code, 422)
        self.assertEqual(self.client.post('/api/engine/select', json={'engine_id': before['engine_id'], 'extra': True}).status_code, 422)
        self.assertEqual(self.client.get('/api/engine/profile/missing/yaml').status_code, 404)
        self.assertEqual(engine_profiles.active(), before)

    def test_switches_reach_both_websockets_and_reports(self):
        with self.client.websocket_connect('/ws/telemetry') as first, self.client.websocket_connect('/ws/telemetry') as second:
            for profile in self.client.get('/api/engine/profiles').json()['profiles']:
                result = self.client.post('/api/engine/select', json={'engine_id': profile['engine_id']}).json()
                meta = result['engine_meta']
                self.assertEqual(meta['engine_id'], profile['engine_id'])
                for socket in (first, second):
                    # Drain at most 50 buffered frames from the previous selection.
                    for _ in range(50):
                        packet = socket.receive_json()
                        if packet['engine_meta']['revision'] >= meta['revision']:
                            break
                    self.assertEqual(packet['active_engine_id'], profile['engine_id'])
                    self.assertEqual(packet['engine_meta']['engine_id'], packet['active_engine_id'])
                    self.assertEqual(packet['engine_meta']['limits'], profile['limits'])
                    self.assertIn('physics_twin_expected', packet)
                    self.assertIn('rul_estimation', packet)
                    self.assertIn('profile_alerts', packet)
                report = self.client.get('/api/report').json()
                self.assertEqual(report['engine_meta']['engine_id'], profile['engine_id'])
                self.assertIn('Reference simulator', report['assessment_scope'])
        # Refresh / new clients discover the server's active selection.
        self.assertEqual(self.client.get('/api/engine/profiles').json()['active_engine_id'], profile['engine_id'])

    def test_noop_switch_keeps_revision_and_metadata(self):
        active = engine_profiles.active()
        again = self.client.post('/api/engine/select', json={'engine_id': active['engine_id']}).json()
        self.assertEqual(again['engine_meta'], active)

    def test_demo_limits_change_classification_without_mutating_data(self):
        telemetry = {'cht_deg_c': 150, 'oil_pressure_psi': 0}
        original = telemetry.copy()
        ae = copy.deepcopy(engine_profiles.profiles['austro_ae300_tapas'])
        rotax = copy.deepcopy(engine_profiles.profiles['rotax_914_heron'])
        self.assertNotIn('cht_deg_c', [item['key'] for item in profile_alerts(telemetry, ae)])
        rotax_alerts = {item['key']: item for item in profile_alerts(telemetry, rotax)}
        self.assertEqual(rotax_alerts['cht_deg_c']['severity'], 'CRITICAL')
        self.assertEqual(rotax_alerts['oil_pressure_psi']['value'], 0)
        self.assertEqual(telemetry, original)

    def test_invalid_ranges_are_rejected(self):
        source = yaml.safe_load(engine_profiles.raw_yaml('austro_ae300_tapas'))
        source['sensor_map']['cht_deg_c']['max'] = 0
        with self.assertRaises(ValidationError):
            EngineProfile.model_validate(source)

    def test_original_control_routes(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        self.assertEqual(self.client.post('/api/scenario', json={'scenario': 'NOMINAL_FLIGHT'}).status_code, 200)
        self.assertEqual(self.client.post('/api/environment', json={'altitude_ft': 2000, 'ambient_temp_c': 25, 'throttle_pct': 60, 'fault_mode': 'NONE'}).status_code, 200)

if __name__ == '__main__':
    unittest.main()
