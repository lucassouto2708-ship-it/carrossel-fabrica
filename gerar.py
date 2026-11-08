"""
Fábrica de carrosséis em lote.

Uso:
    python gerar.py              -> processa TODOS os textos em textos/
    python gerar.py nome         -> processa só textos/nome.txt
    python gerar.py --refazer    -> reprocessa mesmo os que já têm saída

Estrutura:  textos/<nome>.txt   +   fotos/<nome>/  (fotos com QUALQUER nome)
Saída: saida/<nome>/slide_01.jpg ... + legenda.txt
"FOTO: 3" no texto = 3ª foto da pasta (ordem natural do nome do arquivo).
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

RAIZ = Path(__file__).parent
EXT_FOTO = {".jpg", ".jpeg", ".png", ".webp"}


# ---------------------------------------------------------------- parsing
def ler_texto(caminho: Path):
    """Lê texto.txt -> (lista de slides, legenda)."""
    bruto = caminho.read_text(encoding="utf-8-sig")
    legenda = ""
    m = re.split(r"^\s*===\s*LEGENDA\s*===\s*$", bruto, maxsplit=1, flags=re.M | re.I)
    if len(m) == 2:
        bruto, legenda = m[0], m[1].strip()

    slides = []
    for bloco in re.split(r"^\s*---\s*$", bruto, flags=re.M):
        bloco = bloco.strip()
        if not bloco:
            continue
        campos = {"foto": None, "fundo": None, "posicao": "base", "texto": []}
        atual = None
        for linha in bloco.splitlines():
            mm = re.match(r"^\s*(FOTO|FUNDO|POSICAO|POSIÇÃO|TEXTO|TEMA)\s*:\s*(.*)$", linha, re.I)
            if mm:
                chave = mm.group(1).lower().replace("ç", "c").replace("ã", "a")
                valor = mm.group(2).strip()
                if chave == "tema":
                    atual = None
                    continue
                if chave == "texto":
                    campos["texto"] = [valor] if valor else []
                    atual = "texto"
                else:
                    campos[chave] = valor
                    atual = None
            elif atual == "texto" and linha.strip():
                campos["texto"].append(linha.strip())
        if campos["texto"]:
            campos["texto"] = " ".join(campos["texto"])
            slides.append(campos)
    return slides, legenda


# ---------------------------------------------------------------- desenho
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def tokens(texto):
    """Divide em palavras; *palavra* ou *várias palavras* viram destaque."""
    saida, destaque = [], False
    fim_com_espaco = True  # o trecho anterior terminou em espaço (ou é o início)?
    for parte in re.split(r"(\*)", texto):
        if parte == "*":
            destaque = not destaque
            continue
        if not parte:
            continue
        palavras = parte.split()
        # sem espaço entre o trecho anterior e este (ex: *agora*. ) -> cola na palavra anterior
        if palavras and saida and not fim_com_espaco and not parte[0].isspace():
            ant, flag = saida[-1]
            saida[-1] = (ant + palavras.pop(0), flag)
        for p in palavras:
            saida.append((p, destaque))
        fim_com_espaco = parte[-1].isspace()
    return saida


def quebrar(draw, palavras, fonte, largura):
    linhas, atual, w_atual = [], [], 0
    esp = draw.textlength(" ", font=fonte)
    for pal, dest in palavras:
        w = draw.textlength(pal, font=fonte)
        extra = w if not atual else esp + w
        if atual and w_atual + extra > largura:
            linhas.append(atual)
            atual, w_atual = [(pal, dest)], w
        else:
            atual.append((pal, dest))
            w_atual += extra
    if atual:
        linhas.append(atual)
    return linhas


def ajustar_texto(draw, palavras, cfg, largura, altura_max):
    tam = cfg["tamanho_fonte_max"]
    while True:
        fonte = ImageFont.truetype(cfg["fonte"], tam)
        linhas = quebrar(draw, palavras, fonte, largura)
        h_linha = int(tam * 1.18)
        if len(linhas) * h_linha <= altura_max or tam <= cfg["tamanho_fonte_min"]:
            return fonte, linhas, h_linha
        tam -= 4


def foto_cobrindo(caminho, w, h):
    img = Image.open(caminho)
    img = ImageOps.exif_transpose(img).convert("RGB")
    return ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.4))


def gradiente_vertical(w, h, posicao):
    """Camada preta com transparência maior onde fica o texto (legibilidade)."""
    g = Image.new("L", (w, h), 0)
    px = g.load()
    for y in range(h):
        t = y / (h - 1)
        if posicao == "topo":
            a = max(0.0, 1 - t / 0.65)
        elif posicao == "centro":
            a = max(0.0, 1 - abs(t - 0.5) / 0.4)
        else:
            a = max(0.0, (t - 0.35) / 0.65)
        v = int(150 * a)
        for x in range(w):
            px[x, y] = v
    return g


def renderizar_slide(slide, cfg, foto, indice, total):
    W, H, M = cfg["largura"], cfg["altura"], cfg["margem"]
    sobre_foto = foto is not None
    claro = (not sobre_foto) and (slide["fundo"] or "").lower().startswith("clar")

    if sobre_foto:
        base = foto_cobrindo(foto, W, H)
        base = ImageEnhance.Brightness(base).enhance(1 - cfg["escurecer_foto"])
        sombra = gradiente_vertical(W, H, slide["posicao"].lower())
        base.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sombra)
        cor_txt, cor_dest = hex_rgb(cfg["cor_texto"]), hex_rgb(cfg["cor_destaque"])
    elif claro:
        base = Image.new("RGB", (W, H), hex_rgb(cfg["cor_fundo_claro"]))
        cor_txt = hex_rgb(cfg["cor_texto_sobre_claro"])
        cor_dest = hex_rgb(cfg["cor_destaque_sobre_claro"])
    else:
        base = Image.new("RGB", (W, H), hex_rgb(cfg["cor_fundo_escuro"]))
        cor_txt, cor_dest = (255, 255, 255), hex_rgb(cfg["cor_texto"])

    draw = ImageDraw.Draw(base)
    palavras = tokens(slide["texto"])
    area_w = W - 2 * M
    fonte, linhas, h_linha = ajustar_texto(draw, palavras, cfg, area_w, int(H * 0.55))
    bloco_h = len(linhas) * h_linha
    pos = slide["posicao"].lower()
    if pos == "topo":
        y = M + 40
    elif pos == "centro":
        y = (H - bloco_h) // 2
    else:
        y = H - M - 70 - bloco_h

    esp = draw.textlength(" ", font=fonte)
    for linha in linhas:
        x = M
        for pal, dest in linha:
            cor = cor_dest if dest else cor_txt
            if sobre_foto:  # sombra suave
                draw.text((x + 3, y + 4), pal, font=fonte, fill=(0, 0, 0))
            draw.text((x, y), pal, font=fonte, fill=cor)
            x += draw.textlength(pal, font=fonte) + esp
        y += h_linha

    # rodapé: assinatura + indicador de slide
    if cfg.get("assinatura") and (not sobre_foto or cfg.get("assinatura_nos_slides_de_foto")):
        f_peq = ImageFont.truetype(cfg["fonte_pequena"], 28)
        txt = cfg["assinatura"]
        tw = draw.textlength(txt, font=f_peq)
        cor_rod = (120, 140, 170) if not claro else (140, 150, 165)
        draw.text(((W - tw) / 2, H - 70), txt, font=f_peq, fill=cor_rod)
    return base


# ---------------------------------------------------------------- pipeline
def chave_natural(p: Path):
    """Ordena IMG_2 antes de IMG_10 (ordem natural, sem precisar renomear)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def resolver_foto(ref, fotos, pasta_fotos):
    """FOTO: pode ser o nome exato do arquivo OU o número da foto (1 = 1ª da pasta)."""
    exato = pasta_fotos / ref
    if exato.is_file():
        return exato
    m = re.match(r"^0*(\d+)(\.\w+)?$", ref)
    if m:
        n = int(m.group(1))
        if 1 <= n <= len(fotos):
            return fotos[n - 1]
    return None


def processar(txt: Path, cfg, refazer):
    nome = txt.stem
    saida = RAIZ / "saida" / nome
    if saida.exists() and any(saida.glob("slide_*.jpg")) and not refazer:
        print(f"[pula]  {nome} (já tem saída; use --refazer)")
        return
    pasta_fotos = RAIZ / "fotos" / nome
    fotos = (
        sorted((p for p in pasta_fotos.iterdir() if p.suffix.lower() in EXT_FOTO), key=chave_natural)
        if pasta_fotos.is_dir()
        else []
    )
    slides, legenda = ler_texto(txt)
    if not slides:
        print(f"[erro]  {nome}: nenhum slide encontrado em {txt.name}")
        return

    saida.mkdir(parents=True, exist_ok=True)
    cont_auto = 0
    for i, s in enumerate(slides, 1):
        foto = None
        ref = (s["foto"] or "").strip()
        if ref.lower() in ("nenhuma", "none", "-"):
            foto = None
        elif ref:
            foto = resolver_foto(ref, fotos, pasta_fotos)
            if foto is None:
                print(f"[aviso] {nome} slide {i}: foto '{ref}' não encontrada em fotos/{nome}/")
        elif s["fundo"]:
            foto = None  # pediu fundo liso
        elif fotos:
            foto = fotos[cont_auto % len(fotos)]
            cont_auto += 1
        img = renderizar_slide(s, cfg, foto, i, len(slides))
        img.save(saida / f"slide_{i:02d}.jpg", quality=cfg["qualidade_jpg"], subsampling=0)
    if legenda:
        (saida / "legenda.txt").write_text(legenda, encoding="utf-8")
    print(f"[ok]    {nome}: {len(slides)} slides -> saida/{nome}/")


def main():
    cfg = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    refazer = "--refazer" in sys.argv
    pasta_textos = RAIZ / "textos"
    pasta_textos.mkdir(exist_ok=True)
    if args:
        textos = [pasta_textos / (a if a.endswith(".txt") else a + ".txt") for a in args]
        textos = [t for t in textos if t.exists() or print(f"[erro]  não achei {t.name} em textos/")]
    else:
        textos = sorted(pasta_textos.glob("*.txt"))
    if not textos:
        print("Nenhum texto em textos/. Crie textos/<nome>.txt e as fotos em fotos/<nome>/")
        return
    for t in textos:
        processar(t, cfg, refazer or bool(args))


if __name__ == "__main__":
    main()
