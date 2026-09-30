"""Deterministic deployment contract checks; no cluster or secrets required."""
import pathlib
import subprocess
import unittest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
CMD = ['helm', 'template', 'buzz', 'deploy/charts/buzz', '--namespace', 'buzz',
       '-f', 'deploy/tailnet/values.yaml', '-f', 'deploy/tailnet/owner.yaml']

class TailnetContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render = subprocess.check_output(CMD, cwd=ROOT, text=True)
        cls.docs = list(yaml.safe_load_all(cls.render))
        cls.platform = list(yaml.safe_load_all((ROOT / 'deploy/tailnet/platform.yaml').read_text()))
        cls.all = cls.docs + cls.platform

    def resource(self, kind, name):
        return next(d for d in self.all if d['kind'] == kind and d['metadata']['name'] == name)

    def test_render_is_deterministic_and_never_generates_secrets(self):
        self.assertEqual(self.render, subprocess.check_output(CMD, cwd=ROOT, text=True))
        self.assertFalse(any(d['kind'] == 'Secret' for d in self.all))
        eso = self.resource('ExternalSecret', 'buzz-runtime')
        self.assertEqual(eso['spec']['secretStoreRef']['name'], 'onepassword')
        self.assertTrue(all(d['remoteRef']['key'] == 'app-buzz' for d in eso['spec']['data']))
        self.assertNotIn('BUZZ_PRIVATE_KEY', self.render)

    def test_tailnet_only_ingress_and_private_membership(self):
        ingress = self.resource('Ingress', 'buzz')['spec']
        self.assertEqual(ingress['ingressClassName'], 'tailscale')
        self.assertEqual(ingress['tls'], [{'hosts': ['buzz']}])
        target = ingress['rules'][0]['http']['paths'][0]['backend']['service']
        self.assertEqual(target, {'name': 'buzz', 'port': {'number': 3000}})
        relay = self.resource('Deployment', 'buzz')['spec']['template']['spec']['containers'][0]
        env = {e['name']: e for e in relay['env']}
        for key in ['BUZZ_REQUIRE_AUTH_TOKEN', 'BUZZ_REQUIRE_RELAY_MEMBERSHIP']:
            self.assertEqual(env[key]['value'], 'true')
        self.assertEqual(env['RELAY_URL']['value'], 'wss://buzz.tailc69d48.ts.net')
        self.assertRegex(env['RELAY_OWNER_PUBKEY']['value'], r'^[0-9a-f]{64}$')
        for doc in self.all:
            if doc['kind'] == 'Service':
                self.assertNotIn(doc['spec'].get('type'), ['LoadBalancer', 'NodePort'])

    def test_images_pinned_and_data_persistent(self):
        for kind, name in [('Deployment', 'buzz'), ('Deployment', 'buzz-minio'),
                           ('StatefulSet', 'buzz-postgresql'), ('StatefulSet', 'buzz-redis')]:
            pod = self.resource(kind, name)['spec']['template']['spec']
            containers = list(pod['containers'])
            if 'initContainers' in pod and pod['initContainers'] is not None:
                containers.extend(pod['initContainers'])
            for c in containers:
                self.assertRegex(c['image'], r'@sha256:[0-9a-f]{64}$')
        for name in ['buzz-postgresql']:
            claims = self.resource('StatefulSet', name)['spec']['volumeClaimTemplates']
            self.assertEqual(claims[0]['spec']['storageClassName'], 'ceph-rbd')
        for name in ['buzz-minio', 'buzz-redis-data']:
            self.assertEqual(self.resource('PersistentVolumeClaim', name)['spec']['storageClassName'], 'ceph-rbd')
        redis = self.resource('StatefulSet', 'buzz-redis')['spec']['template']['spec']
        data = next(v for v in redis['volumes'] if v['name'] == 'data')
        self.assertEqual(data['persistentVolumeClaim']['claimName'], 'buzz-redis-data')

    def test_missing_owner_rejected(self):
        result = subprocess.run(CMD + ['--set-string', 'ownerPubkey='], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ownerPubkey', result.stderr)

if __name__ == '__main__':
    unittest.main()
