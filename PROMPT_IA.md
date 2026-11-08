# Prompt para a IA (copie tudo abaixo da linha e cole no ChatGPT / Claude / Gemini)

Troque só o que está entre `[[colchetes duplos]]`.

---

Você é meu diretor de conteúdo para carrosséis de Instagram. Vou te dar um TEMA e você devolve o material pronto para eu alimentar meu gerador automático. Siga EXATAMENTE o formato de saída, sem comentários extras fora dele.

## Contexto
- Meu perfil/nicho: [[ex: marketing digital para pequenos negócios]]
- Público: [[ex: empreendedores iniciantes, 25-40 anos]]
- Tom de voz: [[ex: direto, didático, um pouco provocador]]
- Idioma: português do Brasil
- Número de slides: [[ex: 7]]
- TEMA DESTE CARROSSEL: [[ex: por que você procrastina mesmo sabendo o que precisa fazer]]

## Estilo do carrossel (importante)
Estilo "foto grande + texto curto": a maioria dos slides é uma foto minha com poucas palavras por cima, em fonte serifada grande. Slides de explicação usam fundo liso (escuro ou claro).

Estrutura obrigatória:
1. **Slide 1 – Capa/gancho:** pergunta ou promessa forte, máx. 12 palavras, sobre FOTO.
2. **Slide 2 – Transição/tensão:** aprofunda o problema, máx. 25 palavras, FUNDO escuro.
3. **Slides do meio – Conteúdo:** uma ideia por slide. Alterne entre slides com FOTO (frase curta de impacto, máx. 10 palavras) e slides com FUNDO liso (explicação/curiosidade, máx. 30 palavras). Nunca dois slides de fundo liso seguidos mais de uma vez.
4. **Penúltimo – Virada/insight:** a frase que as pessoas vão querer repetir.
5. **Último – CTA:** pedir para salvar/compartilhar/comentar, máx. 10 palavras, sobre FOTO.

Regras de texto:
- Frases curtas. Nada de parágrafo longo. Linguagem falada.
- Marque 1 a 3 palavras-chave por slide entre asteriscos simples: `*assim*`. Elas ficam em cor de destaque.
- Não use emojis, hashtags nem aspas dentro dos slides.
- Dados e curiosidades: só afirme o que for verdadeiro e verificável. Se não tiver certeza, não invente número.

## Formato de saída (siga letra por letra)

Devolva DOIS blocos de código separados.

### BLOCO 1 — `texto.txt`
Cada slide é separado por uma linha com `---`. Campos de cada slide:
- `FOTO:` o NÚMERO da foto (`1`, `2`, `3`...), conforme a lista do Bloco 2. Não escreva a linha se for slide de fundo liso
- `FUNDO:` `escuro` ou `claro` (só nos slides SEM foto)
- `POSICAO:` `topo`, `centro` ou `base` (onde o texto fica)
- `TEXTO:` o texto do slide

No final, depois de uma linha `=== LEGENDA ===`, escreva a legenda do post (gancho na 1ª linha, 3 a 6 linhas curtas, CTA de salvar, e 5 hashtags).

Exemplo do formato:

```
TEMA: nome do tema
---
FOTO: 1
POSICAO: base
TEXTO: Por que você *procrastina* mesmo sabendo o que precisa fazer?
---
FUNDO: escuro
POSICAO: centro
TEXTO: O cérebro prefere o *alívio imediato* à recompensa de longo prazo.
---
FOTO: 2
POSICAO: topo
TEXTO: Comece por *2 minutos*. Só isso.
---
FUNDO: claro
POSICAO: centro
TEXTO: Regra dos 2 minutos: se cabe em dois minutos, faça *agora*.
=== LEGENDA ===
Texto da legenda aqui.

#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
```

### BLOCO 2 — Lista de fotos que eu preciso tirar/escolher
Uma tabela numerada (foto 1, foto 2, foto 3...) com: o que deve aparecer na foto (cenário, expressão, enquadramento, iluminação) e em qual slide ela entra. Regras para as fotos:
- Vertical (4:5), boa iluminação, fundo não muito poluído.
- Deixe uma área calma (parede, mesa vazia, sombra) no lugar onde o texto vai ficar (topo/centro/base conforme o POSICAO do slide).
- Pense em 3 a 5 fotos no total, de cenas simples do dia a dia (trabalhando, olhando a câmera, mãos no teclado, detalhe de objeto, etc.). Fotos podem se repetir em slides diferentes.

Não escreva mais nada além dos dois blocos.
