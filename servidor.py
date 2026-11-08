"""
Painel local da Fábrica de Carrosséis.

    python servidor.py        (ou dê duplo clique em abrir.bat)

Abre http://127.0.0.1:8765 no navegador. Roda só no seu computador.
"""
import io
import json
import mimetypes
import os
import re
import threading
import webbrowser
import zipfile
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from PIL import Image, ImageOps

import gerar

RAIZ = Path(__file__).parent
PORTA = 8765
EXT_FOTO = gerar.EXT_FOTO
CAMPOS_CONFIG = {
    "assinatura": str,
    "assinatura_nos_slides_de_foto": bool,
    "escurecer_foto": float,
    "cor_texto": "cor",
    "cor_destaque": "cor",
    "cor_fundo_escuro": "cor",
    "cor_fundo_claro": "cor",
    "cor_texto_sobre_claro": "cor",
    "cor_destaque_sobre_claro": "cor",
}
LOCK = threading.Lock()


def slug(nome: str) -> str:
    nome = (nome or "").strip().lower()
    nome = re.sub(r"[^a-z0-9_-]+", "-", nome).strip("-")
    return nome[:60]


def extrair_texto(raw: str) -> str:
    """Aceita a resposta inteira da IA: pega só o bloco de código que tem os slides."""
    if "```" in raw:
        blocos = re.findall(r"```[^\n]*\n(.*?)```", raw, re.S)
        cand = [b for b in blocos if re.search(r"^\s*TEXTO\s*:", b, re.M | re.I)]
        if cand:
            return cand[0].strip() + "\n"
    return raw.strip() + "\n"


def pasta_fotos(nome):
    return RAIZ / "fotos" / nome


def lista_fotos(nome):
    p = pasta_fotos(nome)
    if not p.is_dir():
        return []
    return [f.name for f in sorted((x for x in p.iterdir() if x.suffix.lower() in EXT_FOTO), key=gerar.chave_natural)]


def lista_slides(nome):
    p = RAIZ / "saida" / nome
    return sorted(f.name for f in p.glob("slide_*.jpg")) if p.is_dir() else []


def ler_config():
    return json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))


def nomes_carrosseis():
    nomes = set()
    for t in (RAIZ / "textos").glob("*.txt"):
        nomes.add(t.stem)
    if (RAIZ / "fotos").is_dir():
        nomes |= {d.name for d in (RAIZ / "fotos").iterdir() if d.is_dir()}
    return sorted(nomes)


def resumo(nome):
    txt = RAIZ / "textos" / f"{nome}.txt"
    n_slides = len(gerar.ler_texto(txt)[0]) if txt.exists() else 0
    return {
        "nome": nome,
        "fotos": len(lista_fotos(nome)),
        "slides_texto": n_slides,
        "slides_gerados": len(lista_slides(nome)),
    }


def detalhe(nome):
    txt = RAIZ / "textos" / f"{nome}.txt"
    legenda = RAIZ / "saida" / nome / "legenda.txt"
    return {
        **resumo(nome),
        "texto": txt.read_text(encoding="utf-8-sig") if txt.exists() else "",
        "lista_fotos": lista_fotos(nome),
        "lista_slides": lista_slides(nome),
        "legenda": legenda.read_text(encoding="utf-8") if legenda.exists() else "",
    }


def prompt_template():
    md = (RAIZ / "PROMPT_IA.md").read_text(encoding="utf-8")
    return md.split("\n---\n", 1)[1].strip() if "\n---\n" in md else md


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silencia o log
        pass

    # ---------- helpers
    def _send(self, code, body=b"", ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _erro(self, msg, code=400):
        self._send(code, {"erro": msg})

    # ---------- GET
    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path
        try:
            if p in ("/", "/index.html"):
                return self._send(200, (RAIZ / "painel.html").read_bytes(), "text/html; charset=utf-8")
            if p == "/api/carrosseis":
                return self._send(200, [resumo(n) for n in nomes_carrosseis()])
            if p == "/api/carrossel":
                nome = slug(q.get("c"))
                return self._send(200, detalhe(nome)) if nome else self._erro("nome inválido")
            if p == "/api/config":
                cfg = ler_config()
                return self._send(200, {k: cfg.get(k) for k in CAMPOS_CONFIG})
            if p == "/api/prompt":
                return self._send(200, {"template": prompt_template()})
            if p == "/api/zip":
                nome = slug(q.get("c"))
                d = RAIZ / "saida" / nome
                if not d.is_dir():
                    return self._erro("nada gerado ainda", 404)
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
                    for f in sorted(d.iterdir()):
                        z.write(f, f.name)
                return self._send(
                    200, buf.getvalue(), "application/zip",
                    {"Content-Disposition": f'attachment; filename="{nome}.zip"'},
                )
            if p.startswith("/files/"):
                return self._arquivo(p[len("/files/"):], q)
            return self._erro("não encontrado", 404)
        except Exception as e:  # noqa
            return self._erro(str(e), 500)

    def _arquivo(self, rel, q):
        partes = [unquote(x) for x in rel.split("/")]
        if len(partes) != 3 or partes[0] not in ("fotos", "saida"):
            return self._erro("não encontrado", 404)
        tipo, nome, arq = partes
        if slug(nome) != nome or arq != Path(arq).name:
            return self._erro("inválido", 400)
        f = RAIZ / tipo / nome / arq
        if not f.is_file():
            return self._erro("não encontrado", 404)
        if q.get("t"):  # miniatura
            img = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
            img.thumbnail((420, 520))
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=80)
            return self._send(200, buf.getvalue(), "image/jpeg")
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        return self._send(200, f.read_bytes(), ctype)

    # ---------- POST / PUT / DELETE
    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/carrossel":
                nome = slug(json.loads(self._body() or b"{}").get("nome"))
                if not nome:
                    return self._erro("Dê um nome ao carrossel (letras e números).")
                pasta_fotos(nome).mkdir(parents=True, exist_ok=True)
                (RAIZ / "textos").mkdir(exist_ok=True)
                t = RAIZ / "textos" / f"{nome}.txt"
                if not t.exists():
                    t.write_text("", encoding="utf-8")
                return self._send(200, {"nome": nome})
            if u.path == "/api/gerar":
                nome = slug(q.get("c"))
                txt = RAIZ / "textos" / f"{nome}.txt"
                if not nome or not txt.exists() or not txt.read_text(encoding="utf-8").strip():
                    return self._erro("Cole o texto do carrossel antes de gerar.")
                buf = io.StringIO()
                with LOCK, redirect_stdout(buf):
                    gerar.processar(txt, ler_config(), True)
                avisos = [l.strip() for l in buf.getvalue().splitlines() if l.startswith(("[erro]", "[aviso]"))]
                d = detalhe(nome)
                if not d["lista_slides"]:
                    return self._erro(" ".join(avisos) or "Não consegui gerar. Confira o texto.")
                return self._send(200, {**d, "avisos": avisos})
            return self._erro("não encontrado", 404)
        except Exception as e:  # noqa
            return self._erro(str(e), 500)

    def do_PUT(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/texto":
                nome = slug(q.get("c"))
                if not nome:
                    return self._erro("nome inválido")
                (RAIZ / "textos").mkdir(exist_ok=True)
                texto = extrair_texto(self._body().decode("utf-8", "replace")) if self.headers.get("X-Limpar") else (
                    self._body().decode("utf-8", "replace")
                )
                (RAIZ / "textos" / f"{nome}.txt").write_text(texto, encoding="utf-8")
                return self._send(200, {"slides": len(gerar.ler_texto(RAIZ / "textos" / f"{nome}.txt")[0]), "texto": texto})
            if u.path == "/api/foto":
                nome, arq = slug(q.get("c")), Path(q.get("f") or "").name
                if not nome or Path(arq).suffix.lower() not in EXT_FOTO:
                    return self._erro("Só aceito jpg, png ou webp.")
                pasta_fotos(nome).mkdir(parents=True, exist_ok=True)
                (pasta_fotos(nome) / arq).write_bytes(self._body())
                return self._send(200, {"ok": True})
            if u.path == "/api/config":
                novo = json.loads(self._body() or b"{}")
                cfg = ler_config()
                for k, tipo in CAMPOS_CONFIG.items():
                    if k not in novo:
                        continue
                    v = novo[k]
                    if tipo == "cor":
                        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(v)):
                            return self._erro(f"Cor inválida em {k}")
                        cfg[k] = v
                    elif tipo is float:
                        cfg[k] = max(0.0, min(0.9, float(v)))
                    elif tipo is bool:
                        cfg[k] = bool(v)
                    else:
                        cfg[k] = str(v)[:60]
                (RAIZ / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                return self._send(200, {"ok": True})
            return self._erro("não encontrado", 404)
        except Exception as e:  # noqa
            return self._erro(str(e), 500)

    def do_DELETE(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/foto":
                nome, arq = slug(q.get("c")), Path(q.get("f") or "").name
                f = pasta_fotos(nome) / arq
                if nome and f.is_file() and f.suffix.lower() in EXT_FOTO:
                    f.unlink()
                return self._send(200, {"ok": True})
            return self._erro("não encontrado", 404)
        except Exception as e:  # noqa
            return self._erro(str(e), 500)


def main():
    for d in ("fotos", "textos", "saida"):
        (RAIZ / d).mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), H)
    url = f"http://127.0.0.1:{PORTA}"
    print(f"Fábrica de carrosséis rodando em {url}  (Ctrl+C para fechar)")
    if not os.environ.get("CARROSSEL_SEM_NAVEGADOR"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
