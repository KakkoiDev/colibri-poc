import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import remote_access as remote


class RemoteAccessTests(unittest.TestCase):
    def test_loopback_and_cross_origin(self):
        self.assertTrue(remote.allowed({'Host':'127.0.0.1:8766'},8766))
        self.assertFalse(remote.allowed({'Host':'evil.test'},8766))
        self.assertFalse(remote.allowed({'Host':'localhost:8766','Origin':'https://evil.test'},8766,True))

    def test_remote_requires_exact_host_user_and_origin(self):
        with patch.object(remote,'config',return_value={'url':'https://lab.tail.ts.net:9443','users':['owner']}):
            headers={'Host':'lab.tail.ts.net:9443','Tailscale-User-Login':'owner','Origin':'https://lab.tail.ts.net:9443'}
            self.assertTrue(remote.allowed(headers,8766,True))
            for bad in [{'Host':'other.ts.net:9443'},{'Tailscale-User-Login':'other'},{'Tailscale-User-Login':None},{'Origin':'https://evil.test'}]:
                self.assertFalse(remote.allowed(dict(headers,**bad),8766,True))
            self.assertFalse(remote.allowed({'Host':headers['Host']},8766))
