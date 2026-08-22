# Esboço de arquitetura — SGI (base no Trabalho 1.1, preparada para 3D)

> Documento de projeto (sketch). Descreve **como** o sistema será estruturado, não o código final.
> Objetivo: Clean Code + baixo acoplamento + modularização. O núcleo gráfico (domínio) não conhece a GUI.
>
> **Escopo imediato (1.1):** CG 2D com display file (ponto, reta, wireframe), transformada de viewport,
> panning e zoom do window.
>
> **Escopo futuro considerado no desenho** (specs em `docs/trabalhos/`): transformações 2D (1.2),
> rotação de window + coordenadas normalizadas SCN + I/O `.obj` (1.3), clipping + polígono preenchido (1.4),
> curvas 2D (1.5/1.6), **3D: Point3D/Object3D + projeção paralela (1.7) e perspectiva (1.8)**,
> superfícies bicúbicas (1.9/1.10). Os trabalhos 2.0/3.0/4.0 saem do SGI (Blender, shaders, OpenGL) e
> não pressionam esta arquitetura.

## 1. A decisão central: 2D→3D é uma mudança de *pipeline*, não de reescrita

O arco inteiro do módulo 1 converge para **uma única espinha dorsal**: um pipeline de renderização com
estágios fixos. Cada trabalho **insere um estágio** ou **acrescenta um tipo de objeto** — nunca reescreve
o que já existe. Sair de 2D para 3D é **inserir o estágio de projeção**, não trocar o sistema.

```
coords do mundo (2D hoje → 3D no 1.7)
   → [transformações do objeto]         (1.2 2D, 1.7 3D)
   → [normalização / view → SCN]        (1.3: rotação da window mora aqui)
   → [projeção 3D→2D]                    (1.7 paralela, 1.8 perspectiva)   ← estágio que "não existe" em 2D
   → [clipping 2D]                       (1.4; curvas/superfícies 1.5+)
   → [transformada de viewport]          (1.1)
   → desenhar SÓ ponto/linha             (1.1, para sempre — exigência da spec)
```

Consequência de projeto: o controller **não** tem um método `render` monolítico. Tem uma **lista ordenada
de estágios**. Em 2D a lista é `[normalize?, clip, viewport]`. Em 3D vira `[..., project, clip, viewport]`.
Passar de 2D a 3D = inserir um item na lista + trocar o tipo de coordenada. Nada mais.

## 2. Princípios que guiam o desenho

- **Camadas com dependência para dentro:** `gui` → `app` → `domain`. O domínio nunca importa Qt.
- **Uma responsabilidade por módulo.**
- **Matemática pura e testável:** matrizes, projeção e transformada de viewport são funções puras.
  Desenho e eventos Qt ficam nas bordas.
- **Coordenadas homogêneas, dimensão-agnósticas:** um ponto é um vetor homogêneo. Em 2D `[x, y, 1]`,
  em 3D `[x, y, z, 1]`. **Nada de `Point2D` no nome** — a base já nasce genérica para o 1.7 não exigir
  renomear tudo (ver §3.1).
- **O renderer sempre desenha só ponto e linha.** Todo objeto complexo (wireframe, curva, superfície,
  3D projetado) sabe se **decompor em segmentos** antes de chegar no desenho. A restrição da spec
  ("só drawPoint/drawLine") vira a garantia que mantém a GUI trivial para sempre.
- **No premature abstraction:** só criamos os seams que os specs *comprovadamente* exigem (pipeline,
  hierarquia de objetos, estratégia de projeção). Não construímos máquinas 3D agora — deixamos a costura
  pronta e cortada, sem material dentro.

## 3. Mapa de camadas

```
┌───────────────────────────────────────────────────────────────┐
│  gui/            (PyQt — bordas: eventos, pixels, botões)       │
│    main_window.py       janela, menus, lista de objetos         │
│    viewport_widget.py   canvas: SÓ drawPoint/drawLine           │
│    object_dialog.py     diálogo "adicionar objeto" (+cor, +fill)│
│    transform_dialog.py  entrada de transformações (a partir 1.2)│
└───────────────▲───────────────────────────────────────────────┘
                │ depende de
┌───────────────┴───────────────────────────────────────────────┐
│  app/            (orquestração — sem Qt, sem pixels)            │
│    controller.py        estado + monta e roda o pipeline        │
│    render_pipeline.py   lista ordenada de estágios (a espinha)  │
└───────────────▲───────────────────────────────────────────────┘
                │ depende de
┌───────────────┴───────────────────────────────────────────────┐
│  domain/         (núcleo gráfico — Python puro, testável)       │
│    geometry.py          vetor homogêneo n-D + matrizes n×n      │
│    transforms.py        fábricas de matriz (translate/scale/rot)│
│    objects.py           GraphicObject: Point/Line/Wireframe/... │
│    display_file.py      coleção nomeada + cache de coords SCN   │
│    window.py            região de mundo + pan/zoom/rotate       │
│    normalization.py     mundo → SCN (view transform)            │
│    projection.py        3D→2D (estratégia: paralela/perspectiva)│
│    clipping.py          ponto/linha/polígono/curva              │
│    viewport.py          SCN/2D → tela (sem distorcer)           │
│  persistence/    (nome `persistence`, não `io`: `io` colidiria │
│    obj_descriptor.py    com a stdlib) — leitura/escrita .obj    │
│    parser.py            parse de "(x,y[,z]),..."                │
└────────────────────────────────────────────────────────────────┘
```

> **1.1 não cria tudo isto.** Cria só `geometry`, `objects` (3 tipos), `display_file`, `window`, `viewport`,
> `parser`, `controller`, e a GUI mínima. Os demais módulos são **onde** cada trabalho futuro entra — listados
> agora para que o 1.1 já ponha as coisas no lugar certo e nada precise mudar de lugar depois.

## 4. Módulos do domínio

### 4.1 `geometry.py` — dimensão-agnóstico desde o início
- `Point` (não `Point2D`): guarda um vetor homogêneo. Em 2D `(x, y, 1)`, em 3D `(x, y, z, 1)`.
  A dimensão é o tamanho do vetor, não o nome da classe.
- `Vector` / operações e produto por matriz.
- `Matrix` n×n com `multiply`, `compose`.
- **Por que agora:** o 1.7 troca 3 coords por 4 e 3×3 por 4×4. Se o código nunca assumiu "2", essa troca é
  transparente. Este é o seam #1 do plano 2D→3D.

### 4.2 `transforms.py` — o "engine" genérico que o 1.2 pede
- `apply(matrix, obj) -> obj` — rotina única que transforma qualquer objeto (o 1.2 exige exatamente isto).
- Fábricas: `translation(...)`, `scaling(...)`, `rotation(...)`. Assinaturas aceitam 2D hoje; ganham a
  variante 3D (rotação em torno de eixo arbitrário, 1.7) como funções irmãs — sem tocar em `apply`.

### 4.3 `objects.py` — hierarquia que só cresce
```
GraphicObject (abstrata)
  ├── name, type, attributes(color RGB [1.2], filled [1.4])
  ├── world_coords: list[Point]        # coords do mundo, dimensão-agnósticas
  ├── center() -> Point
  ├── transform(matrix)                # delega a transforms.apply
  └── to_segments() -> list[(Point,Point)]   # como o objeto vira linhas p/ desenhar
       ├── Point        (1.1)
       ├── Line         (1.1)
       ├── Wireframe    (1.1)  polígono = lista de pontos ligados
       ├── Curve2D      (1.5/1.6)  amostra a curva e devolve segmentos
       └── Surface      (1.9/1.10) malha de retalhos → segmentos
```
- **`to_segments()` é a chave:** o renderer só sabe desenhar segmentos. Curva, superfície e objeto 3D
  projetado todos entram por esse mesmo método. Adicionar um tipo novo = uma subclasse, zero mudança na GUI.
- Coords são **do mundo** e não conhecem tela nem window.

### 4.4 `display_file.py`
- Coleção ordenada e nomeada de `GraphicObject` (add/remove/get/iterar), nome único.
- **Cache de coordenadas normalizadas (SCN):** o 1.3 exige que a rotação da window **não** altere as coords
  do mundo — ela ocorre na cache ou no desenho. Então o display file guarda, por objeto, as coords em SCN,
  recalculadas quando a window muda. Em 1.1 essa cache é trivial (SCN = mundo); o campo já existe para 1.3
  preencher.

### 4.5 `window.py`
- `Window` — região do mundo visível. Em 1.1: retângulo + `pan`/`zoom`.
- 1.3 acrescenta `rotate(angle)` (a window é tratada como objeto gráfico e girada em WC) e o conceito de
  "para cima" do usuário. 3D (1.7) acrescenta navegação no espaço (VRP/VPN).
- Mantém razão de aspecto → viewport não distorce.

### 4.6 `normalization.py` — o estágio de view (SCN)
- `to_scn(point, window) -> Point`: leva do mundo ao Sistema de Coordenadas Normalizado, incluindo a rotação
  da window. **Em 1.1 é identidade/quase-identidade**; existe para 1.3 preencher sem inserir um estágio novo
  às pressas.

### 4.7 `projection.py` — o estágio que materializa o 3D (seam #2)
- Interface `Projection.project(point) -> Point2D`.
- `ParallelProjection` (1.7) e `PerspectiveProjection` (1.8, centro de projeção variável).
- **Não existe em 1.1** — o arquivo pode nem ser criado ainda. O que existe hoje é o **lugar dele no
  pipeline** (§5): um estágio opcional. Quando o 1.7 chegar, cria-se a classe e insere-se o estágio; nada
  antes dele muda.

### 4.8 `clipping.py`
- Clipagem de ponto, reta (2 técnicas selecionáveis: C-S / L-B / NLN), polígono, curva (1.5).
- Estágio do pipeline **antes** da viewport (1.4: viewport recebe só o que sobrou do clip).
- Em 1.1 ausente; entra como estágio no 1.4.

### 4.9 `viewport.py`
- `ViewportTransform` — SCN/2D → pixels. Fórmula window→viewport, **y invertido**.
- **Anti-distorção:** mesma escala em x e y (fit isotrópico). Requisito "quadrado continua quadrado".
- Recebe `Point` já projetado/normalizado; nunca chama Qt.

### 4.10 `persistence/parser.py` e `persistence/obj_descriptor.py`
> Módulo chamado `persistence` (não `io`) para não sombrear a stdlib `io` do Python.
- `parser.parse_coordinates(s)`: padrão `(x1,y1),(x2,y2),...` via `list(eval(s))` (exigência da spec).
  Naturalmente aceita a 3ª coordenada no 1.7 e o separador `;` de matrizes no 1.9. `eval` isolado num só
  módulo mantém o resto limpo.
- `obj_descriptor` (a partir do 1.3): `DescritorOBJ` transcreve cada objeto para Wavefront `.obj` (nome,
  tipo, vértices, arestas) e lê de volta. Módulo de persistência separado do domínio geométrico.

## 5. Camada de aplicação — a espinha dorsal

### `app/render_pipeline.py`
Uma **lista ordenada de estágios**, cada estágio uma função pura `list[Primitive] -> list[Primitive]`.

```
Pipeline 2D (1.1):        [ to_segments, normalize(≈id), viewport ]
+ clipping (1.4):         [ to_segments, normalize, CLIP, viewport ]
+ 3D (1.7/1.8):           [ to_segments, normalize, PROJECT, clip, viewport ]
```
Trocar 2D→3D = **inserir `PROJECT`** e alimentar o pipeline com coords 3D. O código de cada estágio
existente não muda. Este arquivo é o coração do "sim, a arquitetura suporta 3D".

### `app/controller.py`
Orquestra sem tocar em pixels. Estado: `DisplayFile` + `Window` (+ `Projection` a partir do 1.7).
- `add_object(name, type, raw, attributes)` → parser → `GraphicObject` → display file.
- `transform_object(name, matrix)` (1.2) → `transforms.apply`.
- `pan/zoom/rotate_window(...)` → delega ao `Window`, invalida cache SCN.
- `render(viewport_size) -> list[DrawCommand]` → roda o pipeline e devolve **comandos neutros**
  (`DrawPoint`, `DrawLine`), nunca chamadas Qt.

## 6. Camada GUI (PyQt — só nas bordas)
- `viewport_widget.py` — `paintEvent` pede `controller.render(...)` e desenha **só** `drawPoint`/`drawLine`.
  Captura mouse/scroll → pan/zoom/rotate.
- `object_dialog.py` — nome, tipo, coordenadas (`(x,y[,z]),...`), cor (1.2), arame/preenchido (1.4).
- `transform_dialog.py` — lista de transformações a compor (1.2).
- `main_window.py` — `QMainWindow` monta tudo.

A GUI é imune à passagem 2D→3D: ela só executa `DrawCommand`s. Um cubo projetado chega como os mesmos
`DrawLine` que um quadrado.

## 7. Layout de arquivos proposto

```
src/
  domain/
    geometry.py  transforms.py  objects.py  display_file.py
    window.py    normalization.py  projection.py  clipping.py  viewport.py
  persistence/            # nome evita colisão com a stdlib `io`
    parser.py    obj_descriptor.py
  app/
    controller.py  render_pipeline.py
  gui/
    main_window.py  viewport_widget.py  object_dialog.py  transform_dialog.py
  main.py
tests/
  test_geometry.py  test_viewport.py  test_display_file.py  test_parser.py
```
> Para o 1.1, criar só o subconjunto da §3 nota. Os arquivos restantes nascem no trabalho que os exige,
> **no lugar já reservado**.

## 8. Resposta direta: a arquitetura suporta 2D→3D?

**Sim, e por construção.** A passagem 2D→3D toca exatamente **dois seams**, ambos previstos:

1. **Coordenada dimensão-agnóstica** (`geometry.Point` = vetor homogêneo, matriz n×n).
   2D→3D = 3 componentes viram 4, 3×3 vira 4×4. Nenhum nome `2D` para renomear.
2. **Estágio de projeção no pipeline** (`projection.py` + inserir `PROJECT`).
   O 3D é literalmente "um estágio a mais na lista". Todo o resto — display file, clipping, viewport,
   GUI, desenho ponto/linha — permanece igual.

O que garante que os seams bastem:
- `to_segments()` — todo objeto (2D, 3D, curva, superfície) vira segmentos antes do desenho; a GUI nunca sabe
  a dimensão.
- pipeline como lista — inserir/remover estágio sem reescrever método.
- `DrawCommand` neutro — GUI desacoplada da dimensão e da biblioteca.

**Não-ideal evitado:** a versão anterior deste sketch usava `Point2D` e um mapeamento mundo→viewport em um
salto só, sem lugar para a projeção. Isso forçaria, no 1.7, renomear tipos por todo o código e **inserir um
estágio inexistente** no meio do render — refactor caro. A versão atual pré-corta esses dois pontos e mantém
o 1.1 igualmente pequeno.
