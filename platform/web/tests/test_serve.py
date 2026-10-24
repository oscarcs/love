import gzip
import importlib.util
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location('web_serve', Path(__file__).parents[1] / 'serve.py')
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)


class ServeTest(unittest.TestCase):
    def test_compression_negotiation_and_mime(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = b'\0asm' + b'x' * 100
            (Path(directory) / 'love.wasm').write_bytes(payload)
            (Path(directory) / 'love.wasm.gz').write_bytes(gzip.compress(payload))
            with ThreadingHTTPServer(('127.0.0.1', 0), partial(serve.Handler, directory=directory)) as server:
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    url = 'http://127.0.0.1:' + str(server.server_port) + '/love.wasm?v=test'
                    for encoding, compressed in [('gzip', True), ('gzip;q=0, identity', False), ('identity', False)]:
                        with urlopen(Request(url, headers={'Accept-Encoding': encoding})) as response:
                            self.assertEqual(response.headers['Content-Type'], 'application/wasm')
                            self.assertEqual(response.headers['Vary'], 'Accept-Encoding')
                            self.assertEqual(response.headers['Cache-Control'], 'no-cache')
                            data = response.read()
                            if compressed:
                                self.assertEqual(response.headers['Content-Encoding'], 'gzip')
                                data = gzip.decompress(data)
                            else:
                                self.assertIsNone(response.headers['Content-Encoding'])
                            self.assertEqual(data, payload)
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == '__main__':
    unittest.main()
