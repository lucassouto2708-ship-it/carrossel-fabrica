# Fábrica de carrosséis — como usar

## O jeito fácil: o painel
Dê **duplo clique em `abrir.bat`**. O navegador abre o painel com tudo:
1. **Aba Prompt da IA:** preenche nicho, público, tom e tema e copia o prompt pronto.
2. **Aba Carrosséis:** cria o carrossel, arrasta as fotos, cola a resposta da IA (pode colar a resposta inteira) e clica em **Gerar carrossel**.
3. Os slides aparecem na tela; baixe tudo em .zip e copie a legenda.
4. **Aba Estilo:** assinatura, cores e escurecimento da foto.

Para fechar, feche a janela preta. O resto deste arquivo explica a estrutura de pastas por baixo do painel.

## Estrutura (duas pastas separadas, sem renomear foto)
```
carrossel-fabrica/
├── fotos/
│   └── nome-do-carrossel/      <- joga as fotos aqui, com QUALQUER nome (IMG_1234.jpg etc.)
├── textos/
│   └── nome-do-carrossel.txt   <- cola o texto que a IA mandou (mesmo nome da pasta de fotos)
└── saida/                      <- os slides prontos aparecem aqui
```
O que liga os dois é o **nome**: `textos/chacara-em-familia.txt` usa as fotos de `fotos/chacara-em-familia/`.

## Fluxo (por carrossel)
1. Abra o `PROMPT_IA.md`, troque os `[[colchetes]]` e cole na IA.
2. A IA devolve o **Bloco 1** (texto) e o **Bloco 2** (lista numerada de fotos).
3. Salve o Bloco 1 em `textos/<nome>.txt`.
4. Crie `fotos/<nome>/` e jogue as fotos lá, **na ordem da lista** do Bloco 2.
   - "Foto 1" = a primeira da pasta em ordem de nome, "foto 2" = a segunda, e assim por diante.
   - Se a ordem do nome não bate, é só trocar os números `FOTO:` no texto.
5. Rode `python gerar.py`.
6. Slides em `saida/<nome>/slide_01.jpg ...` + `legenda.txt`.

## Em massa
Vários `.txt` em `textos/` + as pastas de fotos correspondentes, e um único `python gerar.py` processa tudo.
- Quem já tem saída é pulado. Para refazer um: `python gerar.py nome`. Para refazer todos: `python gerar.py --refazer`.

## Ajustes (config.json)
Fonte, cores, escurecimento da foto, assinatura (`@seuperfil`) e tamanhos.

## Regras do texto
- `---` separa slides. `=== LEGENDA ===` começa a legenda.
- `FOTO: 3` -> 3ª foto da pasta. Também aceita o nome exato do arquivo (`FOTO: IMG_4001.jpg`).
- `FOTO` omitido e sem `FUNDO:` -> usa as fotos em ordem.
- `FUNDO: escuro|claro` -> slide liso. `FOTO: nenhuma` também força liso.
- `*palavra*` -> destaque em cor.
- `POSICAO: topo|centro|base`.
