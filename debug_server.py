#!/usr/bin/env python3
"""
debug_server.py  –  DnD 调试前端服务器
用法: python debug_server.py [port]   默认端口 8765
访问: http://localhost:8765
"""
import json
import os
import subprocess
import sys
import threading
import uuid
import tempfile
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
PKG_DIR   = os.path.join(BASE_DIR, "package")
MODES_DIR = os.path.join(PKG_DIR, "modes")
HTML_FILE = os.path.join(BASE_DIR, "debug.html")

# ── Job store ──────────────────────────────────────────────────────────────────
# job_id → { "status": "running"|"done"|"error", "lines": [...], "lock": Lock }
JOBS = {}
JOBS_LOCK = threading.Lock()

def _run_job(job_id, cmd):
    job = JOBS[job_id]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    temp_files = []
    for i, part in enumerate(cmd[:-1]):
        if part == "--context-selection-file":
            temp_files.append(cmd[i + 1])
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=BASE_DIR,
            env=env,
        )
        for line in iter(proc.stdout.readline, ""):
            with job["lock"]:
                job["lines"].append(line.rstrip("\n"))
        proc.wait()
        with job["lock"]:
            job["lines"].append(f"\n[退出码: {proc.returncode}]")
            job["status"] = "done"
    except Exception as e:
        with job["lock"]:
            job["lines"].append(f"[服务器错误] {e}")
            job["status"] = "error"
    finally:
        for path in temp_files:
            try:
                if os.path.abspath(path).startswith(os.path.abspath(BASE_DIR) + os.sep):
                    os.remove(path)
            except Exception:
                pass


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *_):
        pass  # 静默默认日志

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        p  = urlparse(self.path)
        qs = parse_qs(p.query)

        if p.path in ("/", "/debug.html"):
            try:
                body = open(HTML_FILE, "rb").read()
            except FileNotFoundError:
                self._send_json({"error": "debug.html not found"}, 404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif p.path == "/api/files":
            try:
                files = sorted(f for f in os.listdir(PKG_DIR) if f.endswith(".json"))
            except FileNotFoundError:
                files = []
            self._send_json(files)

        elif p.path == "/api/file":
            name = os.path.basename(unquote(qs.get("name", [""])[0]))
            if not name:
                self._send_json({"error": "missing name"}, 400)
                return
            fp = os.path.join(PKG_DIR, name)
            if not os.path.isfile(fp):
                self._send_json({"error": "file not found"}, 404)
                return
            try:
                data = json.load(open(fp, encoding="utf-8"))
                self._send_json(data)
            except json.JSONDecodeError as e:
                self._send_json({"error": f"JSON parse error: {e}"}, 500)

        elif p.path == "/api/modes":
            modes = []
            if os.path.isdir(MODES_DIR):
                for fname in sorted(os.listdir(MODES_DIR)):
                    if fname.endswith(".json"):
                        key = fname[:-5]
                        try:
                            m = json.load(open(os.path.join(MODES_DIR, fname), encoding="utf-8"))
                            modes.append({
                                "key":         key,
                                "name":        m.get("name", key),
                                "description": m.get("description", ""),
                            })
                        except Exception:
                            pass
            self._send_json(modes)

        elif p.path == "/api/job":
            job_id = qs.get("id", [""])[0]
            offset = int(qs.get("offset", ["0"])[0])
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self._send_json({"error": "job not found"}, 404)
                return
            with job["lock"]:
                lines = job["lines"][offset:]
                status = job["status"]
                total = len(job["lines"])
            self._send_json({"status": status, "lines": lines, "offset": total})

        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        p = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n)) if n else {}
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, 400)
            return

        if p.path == "/api/patch_field":
            file_name = os.path.basename(body.get("file", ""))
            path      = body.get("path", [])
            value     = body.get("value")
            if not file_name or not isinstance(path, list) or len(path) == 0:
                self._send_json({"error": "missing or invalid file/path"}, 400)
                return
            fp = os.path.join(PKG_DIR, file_name)
            # Guard: resolved path must stay within PKG_DIR
            if not os.path.abspath(fp).startswith(os.path.abspath(PKG_DIR) + os.sep):
                self._send_json({"error": "invalid file"}, 400)
                return
            if not os.path.isfile(fp):
                self._send_json({"error": "file not found"}, 404)
                return
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                node = data
                for key in path[:-1]:
                    try:
                        node = node[int(key)] if isinstance(node, list) else node[key]
                    except (KeyError, IndexError, ValueError) as e:
                        self._send_json({"error": f"invalid path segment {key!r}: {e}"}, 400)
                        return
                last = path[-1]
                try:
                    if isinstance(node, list):
                        node[int(last)] = value
                    else:
                        node[last] = value
                except (IndexError, ValueError) as e:
                    self._send_json({"error": f"invalid path segment {last!r}: {e}"}, 400)
                    return
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif p.path == "/api/run":
            script = os.path.join(BASE_DIR, "demo_advance_day.py")
            cmd = [sys.executable, "-u", script]
            if body.get("player_action"):
                cmd.append(body["player_action"])
            if body.get("unlock_protected"):
                cmd.append("--unlock-protected")
            if body.get("mode"):
                cmd += ["--mode", body["mode"]]
            if body.get("direct_instruction"):
                cmd += ["--direct-instruction", body.get("direct_instruction")]

            pins = body.get("pins")
            if isinstance(pins, list) and pins:
                fd, sel_path = tempfile.mkstemp(prefix="dnd_context_", suffix=".json", dir=BASE_DIR, text=True)
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump({"pins": pins}, f, ensure_ascii=False, indent=2)
                    cmd += ["--context-selection-file", sel_path]
                except Exception:
                    try:
                        os.close(fd)
                    except Exception:
                        pass
                    raise

            if body.get("game_state_file"):
                cmd += ["--game-state-file", body["game_state_file"]]

            # Create job, launch in background thread, return job_id immediately
            job_id = str(uuid.uuid4())
            job = {"status": "running", "lines": [], "lock": threading.Lock()}
            with JOBS_LOCK:
                JOBS[job_id] = job
            t = threading.Thread(target=_run_job, args=(job_id, cmd), daemon=True)
            t.start()
            self._send_json({"job_id": job_id})

        else:
            self._send_json({"error": "not found"}, 404)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadedHTTPServer(("", port), Handler)
    print(f"DnD 调试服务器已启动")
    print(f"  访问: http://localhost:{port}")
    print(f"  Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
