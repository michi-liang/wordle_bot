"""Serve the deterministic browser game at http://127.0.0.1:8000/."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial


def main():
    directory = Path(__file__).resolve().parent / 'web'
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(('127.0.0.1', 8000), handler)
    print('Running on http://127.0.0.1:8000/ (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
