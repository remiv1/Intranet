"""Tests Nginx isolés, exécutables depuis l'hôte sans base ni application réelle."""

import http.client
import json
import shutil
import ssl
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('docker'), 'Docker requis sur l’hôte pour ce test Nginx.')
class TestNginxMaintenance(unittest.TestCase):
    """Proxy et application simulée sur un réseau Docker temporaire privé."""

    @classmethod
    def docker(cls, *arguments: str) -> str:
        """Exécute une commande Docker et retourne la sortie standard."""
        result = subprocess.run(['docker', *arguments], capture_output=True, text=True,
                                check=True, timeout=40)
        return result.stdout.strip()

    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory(prefix='intranet-maintenance-test-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.prefix = 'intranet-maintenance-test-' + uuid4().hex[:12]
        cls.backend = cls.prefix + '-web'
        cls.proxy = cls.prefix + '-proxy'
        cls.addClassCleanup(cls.cleanup_containers)
        assets = cls.root / 'pages'
        assets.mkdir()
        for filename in ('outage.html', 'planned.html', 'status.css'):
            shutil.copyfile(ROOT / 'app/nginx/maintenance' / filename, assets / filename)
        cls.flag = assets / 'maintenance.enabled'
        certs = cls.root / 'certs'
        certs.mkdir()
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=localhost', '-keyout', str(certs / 'intraraudiere.key'),
            '-out', str(certs / 'intraraudiere.crt'),
        ], check=True, capture_output=True, timeout=30)
        backend_config = cls.root / 'web.conf'
        backend_config.write_text(
            'events {} http { server { listen 5000; '
            'location / { return 200 "application-test"; } '
            'location /not-found { return 404 "application-not-found"; } '
            'location /error-500 { return 500 "application-error"; } '
            'location /error-502 { return 502 "upstream-error"; } '
            'location /error-503 { return 503 "upstream-error"; } '
            'location /error-504 { return 504 "upstream-error"; } } }', encoding='utf-8',
        )
        proxy_config = cls.root / 'nginx.conf'
        proxy_config.write_text((ROOT / 'app/nginx/nginx.conf').read_text(encoding='utf-8').replace(
            'proxy_pass $web_upstream;', 'proxy_connect_timeout 1s; proxy_pass $web_upstream;'
        ), encoding='utf-8')
        cls.docker('network', 'create', cls.prefix)
        cls.docker('run', '-d', '--pull=never', '--name', cls.backend, '--network', cls.prefix,
                   '--network-alias', 'web', '-v', f'{backend_config}:/etc/nginx/nginx.conf:ro',
                   '--entrypoint', 'nginx', 'nginx:latest', '-g', 'daemon off;')
        cls.docker(
            'run', '-d', '--pull=never', '--name', cls.proxy, '--network', cls.prefix,
            '-p', '127.0.0.1::443', '-p', '127.0.0.1::80',
            '-v', f'{proxy_config}:/etc/nginx/nginx.conf:ro',
            '-v', f'{ROOT / "app/nginx/maintenance.conf"}:/etc/nginx/maintenance.conf:ro',
            '-v', f'{assets}:/usr/share/nginx/_maintenance:ro',
            '-v', f'{ROOT / "app/static/img/favicone.svg"}:/usr/share/nginx/favicone.svg:ro',
            '-v', f'{certs}:/etc/nginx/certs:ro', '--entrypoint', 'nginx',
            'nginx:latest', '-g', 'daemon off;',
        )
        cls.https_port = int(cls.docker('port', cls.proxy, '443/tcp').rsplit(':', 1)[1])
        cls.http_port = int(cls.docker('port', cls.proxy, '80/tcp').rsplit(':', 1)[1])
        deadline = time.monotonic() + 10
        while True:
            try:
                if cls.request('/')[0] == 200:
                    break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
            if time.monotonic() >= deadline:
                raise RuntimeError('Le proxy Nginx de test ne répond pas.')

    @classmethod
    def cleanup_containers(cls) -> None:
        """Nettoie les conteneurs Docker utilisé pour le test."""
        for command in (['rm', '-f', cls.proxy, cls.backend], ['network', 'rm', cls.prefix]):
            subprocess.run(['docker', *command], capture_output=True, check=False, timeout=30)

    @classmethod
    def request(
        cls,
        path: str,
        headers: dict[str, str] | None = None,
        method: str = 'GET',
        tls: bool = True,
        timeout: int = 5,
    ) -> tuple[int, dict[str, str], bytes]:
        """Effectue une requête HTTP ou HTTPS vers le proxy Nginx de test."""
        if tls:
            connection = http.client.HTTPSConnection(
                '127.0.0.1',
                cls.https_port,
                context=ssl._create_unverified_context(), # type: ignore # pylint: disable=W0212
                timeout=timeout,
            )
        else:
            connection = http.client.HTTPConnection('127.0.0.1', cls.http_port, timeout=timeout)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, {
                name.lower(): value for name, value in response.getheaders()
                }, response.read()
        finally:
            connection.close()

    def tearDown(self) -> None:
        """Nettoie les fichiers temporaires après chaque test."""
        self.flag.unlink(missing_ok=True)

    def test_normal_requests_and_redirect_remain_unchanged(self) -> None:
        """Teste que les requêtes normales et les redirections restent inchangées."""
        status, headers, body = self.request('/')
        self.assertEqual((status, body), (200, b'application-test'))
        self.assertNotIn('cache-control', headers)
        self.assertEqual(self.request('/not-found')[0], 404)
        self.assertEqual(self.request('/error-500')[0], 500)
        status, headers, _body = self.request('/example?tab=contacts', tls=False)
        self.assertEqual(status, 301)
        self.assertTrue(headers['location'].startswith('https://'))
        self.assertTrue(headers['location'].endswith('/example?tab=contacts'))

    def test_automatic_fallback_for_gateway_errors(self) -> None:
        """Teste le basculement automatique en cas d'erreurs de passerelle."""
        for status_code in (502, 503, 504):
            with self.subTest(status=status_code):
                status, headers, body = self.request(f'/error-{status_code}')
                self.assertEqual(status, 503)
                self.assertIn('text/html', headers['content-type'])
                self.assertEqual(headers['cache-control'], 'no-store')
                self.assertIn(b'Service indisponible', body)

    def test_json_is_selected_by_headers_only(self) -> None:
        """Teste que le format JSON est sélectionné uniquement par les en-têtes HTTP."""
        for headers in ({'Accept': 'application/json'},
                        {'Accept': 'text/html, application/problem+json'},
                        {'Content-Type': 'application/json; charset=utf-8'}):
            with self.subTest(headers=headers):
                status, response_headers, body = self.request('/error-503', headers, method='POST')
                self.assertEqual(status, 503)
                self.assertIn('application/json', response_headers['content-type'])
                self.assertEqual(json.loads(body)['error'], 'intranet_unavailable')
                self.assertEqual(response_headers['cache-control'], 'no-store')
        self.flag.touch()
        self.assertIn(b'Maintenance en cours', self.request('/vpn/api/state')[2])
        self.assertEqual(
            json.loads(self.request('/anywhere', {'Accept': 'application/json'})[2])['error'],
            'intranet_maintenance',
        )

    def test_manual_mode_and_assets_without_restart(self) -> None:
        """Teste le mode manuel et l'accès aux assets sans redémarrage."""
        self.flag.touch()
        for tls in (False, True):
            for method in ('GET', 'POST'):
                status, headers, body = self.request('/anywhere?next=home', method=method, tls=tls)
                self.assertEqual(status, 503)
                self.assertEqual(headers['cache-control'], 'no-store')
                self.assertIn(b'Maintenance en cours', body)
        self.assertEqual(self.request('/_maintenance/status.css')[0], 200)
        status, headers, body = self.request('/_maintenance/favicone.svg')
        self.assertEqual(status, 200)
        self.assertIn('image/svg+xml', headers['content-type'])
        self.assertEqual(body, (ROOT / 'app/static/img/favicone.svg').read_bytes())
        self.assertEqual(self.request('/_maintenance/planned.html')[0], 404)
        self.assertEqual(self.request('/_maintenance/outage.json')[0], 404)
        self.flag.unlink()
        self.assertEqual(self.request('/')[0], 200)

    def test_unreachable_application_uses_static_page(self) -> None:
        """Teste que l'application inaccessible utilise la page statique."""
        self.docker('stop', self.backend)
        try:
            status, headers, body = self.request('/', timeout=90)
            self.assertEqual(status, 503)
            self.assertIn(b'Service indisponible', body)
            self.assertEqual(headers['cache-control'], 'no-store')
        finally:
            self.docker('start', self.backend)


if __name__ == '__main__':
    unittest.main()
