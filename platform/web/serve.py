"""Local release-package preview with gzip negotiation and correct Wasm MIME type."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    compressed = False

    def send_head(self):
        self.compressed = False
        path = Path(super().translate_path(self.path))
        # Parse q=0 too; clients may explicitly reject gzip.
        encodings = {}
        for entry in self.headers.get('Accept-Encoding', '').split(','):
            parts = entry.strip().lower().split(';')
            try:
                encodings[parts[0]] = next((float(p.strip()[2:]) for p in parts[1:] if p.strip().startswith('q=')), 1)
            except ValueError:
                encodings[parts[0]] = 0
        if path.is_file() and Path(str(path) + '.gz').is_file() and encodings.get('gzip', encodings.get('*', 0)) > 0:
            self.compressed = True
        return super().send_head()

    def translate_path(self, path):
        result = super().translate_path(path)
        return result + '.gz' if self.compressed else result

    def guess_type(self, path):
        if self.compressed:
            path = path[:-3]
        if path.endswith('.wasm'):
            return 'application/wasm'
        return super().guess_type(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Vary', 'Accept-Encoding')
        if self.compressed:
            self.send_header('Content-Encoding', 'gzip')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--port', type=int, default=8123)
    parser.add_argument('--bind', default='127.0.0.1')
    args = parser.parse_args()
    with ThreadingHTTPServer((args.bind, args.port), partial(Handler, directory=str(args.directory.resolve()))) as server:
        print('Preview at http://' + args.bind + ':' + str(args.port), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
