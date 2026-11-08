# Fábrica de Carrosséis

Gera carrosséis de Instagram no estilo "foto grande + frase curta". Roda inteiro no navegador, no computador ou no celular. Não precisa instalar nada.

## Como usar

1. **Prompt da IA:** na aba "Prompt da IA", preencha nicho, público, tom e tema. Copie o prompt e cole no ChatGPT, Claude ou Gemini.
2. **Fotos e texto:** na aba "Carrosséis", crie um carrossel, arraste as fotos (qualquer nome de arquivo serve) e cole a resposta da IA. Pode colar a resposta inteira, ele separa só os slides.
3. **Gerar:** clique em "Gerar carrossel" e baixe os slides ou o .zip.

As fotos e os textos ficam só no seu navegador (IndexedDB). Nada é enviado para servidor nenhum.

## Onde está o site

O site fica na pasta [`docs/`](docs/) e é publicado pelo GitHub Pages.
Para ativar: **Settings → Pages → Branch: `main`, pasta `/docs` → Save**.

## Formato do texto

```
---
FOTO: 1
POSICAO: base
TEXTO: Frase com *destaque* em cor
---
FUNDO: escuro
POSICAO: centro
TEXTO: Slide liso, sem foto
=== LEGENDA ===
Legenda do post e #hashtags
```

- `FOTO: 3` é a 3ª foto da lista (as setas ‹ › mudam a ordem).
- `FUNDO: escuro` ou `claro` cria slide liso.
- `POSICAO:` topo, centro ou base.
- `*palavra*` fica em cor de destaque.

## Versão de linha de comando (opcional)

Para gerar em lote pelo computador, existe o `gerar.py` (Python + Pillow):
coloque `textos/<nome>.txt` e `fotos/<nome>/` e rode `python gerar.py`.
O modelo do prompt está em `PROMPT_IA.md` (a cópia usada pelo site é `docs/prompt.txt`; se editar um, copie para o outro).
