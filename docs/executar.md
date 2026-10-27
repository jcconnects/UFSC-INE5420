# Como executar o SGI

Guia completo para rodar o Sistema Gráfico Interativo (Trabalho 1.1+) e sua suíte de testes.

## Pré-requisitos

- **[uv](https://docs.astral.sh/uv/)** — gerenciador de pacotes/ambiente Python. Instalação:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
  # ou: brew install uv
  ```
- O uv cuida do resto: baixa a versão certa do Python e cria o ambiente virtual sozinho.
  Não é preciso instalar Python nem criar `venv` à mão.

## Dependências

Declaradas em [`pyproject.toml`](../pyproject.toml):

- **Runtime:** `PyQt6` — GUI.
- **Dev:** `pytest` — testes.

A primeira execução de qualquer comando `uv run` resolve e instala tudo automaticamente em `.venv/`
e grava o lock em `uv.lock`. Para forçar a instalação antes de rodar:

```bash
uv sync
```

## Rodar a aplicação

```bash
uv run python src/main.py
```

Abre a janela do SGI. A interface tem:

- **Canvas (esquerda):** área de desenho. A viewport desenha **apenas com ponto e linha**
  (requisito da spec — nada de `drawPolygon`).
- **Barra lateral (direita):** lista de objetos, botão **Add object** e controles de **pan/zoom**.

### Interações

| Ação | Como |
|------|------|
| **Adicionar objeto** | Botão *Add object* → informe nome, tipo (point/line/wireframe) e coordenadas |
| **Pan (teclas)** | Botões *Left/Right/Up/Down* na barra lateral |
| **Pan (mouse)** | Arrastar com o **botão do meio** do mouse sobre o canvas |
| **Zoom (botões)** | *Zoom in* / *Zoom out* |
| **Zoom (mouse)** | **Scroll** do mouse sobre o canvas |
| **Orbitar (3D, 1.7)** | Arrastar com o **botão esquerdo** sobre o canvas: gira a window (yaw/pitch) em torno do VRP |
| **Rotacionar a window (1.7)** | Sidebar *Window rotation*: eixo (*Roll* = VPN, *Pitch*, *Yaw*), ângulo, *Rotate window* / *Rotate opposite* |
| **Reset view (1.7)** | Botão *Reset view*: volta VRP, VPN, VUP e zoom iniciais |
| **Transformar objeto** | Selecione na lista → *Transform*: translação (dx, dy, dz), escala (sx, sy, sz) e rotação em torno do eixo X/Y/Z ou de um eixo arbitrário, passando pelo centro do objeto, pela origem ou por um ponto |
| **Modelos 3D** | *Samples → 3D models* (eixos, cubo, pirâmide, paralelepípedo, casa 3D, rua, superfície de Bézier) |
| **Projeção (1.8)** | Sidebar *Projection*: *Parallel orthogonal* (a do 1.7, padrão) ou *Perspective* |
| **Centro de projeção (1.8)** | Slider ou campo *COP distance d* (só em perspectiva): d curto = grande angular, d longo = teleobjetiva. O COP e o campo de visão aparecem na margem inferior do canvas |
| **Superfície de Bézier (1.9)** | *Add object* → tipo *surface*: pontos de controle 16 a 16, linhas da matriz separadas por `;` (ver abaixo); ou *Samples → 3D models → Bezier Surface* (3 retalhos, lida de um `.obj`) |

### Perspectiva (Trabalho 1.8)

O centro de projeção (COP) é virtual: fica atrás da window, na normal que passa pelo centro dela, a uma
distância `d` do lado do observador (`COP = VRP + d·VPN`), e acompanha a window na navegação. O que está no
plano da window aparece igual nas duas projeções; o que está além encolhe e o que está entre a window e o COP
cresce. O clipping continua 2D, contra a window, depois da projeção.

Roteiro rápido:

1. *Samples → 3D models → Street* (rua com prédios, meio-fio e faixas recuando em −z) — de frente, na
   paralela, a profundidade some.
2. *Projection → Perspective*: as arestas ao longo de z convergem para o ponto de fuga no centro.
3. Arraste o slider *COP distance d*: para a esquerda (*wide-angle*, d curto) a convergência fica forte; para
   a direita (*telephoto*, d longo) a profundidade achata e a imagem tende à paralela.
4. *File → Import .obj...* com `samples/3d/parallelepiped.obj` (ou *Samples → 3D models → Parallelepiped*)
   carrega o paralelepípedo de um arquivo; orbite com o botão esquerdo para vê-lo em perspectiva.

### Superfícies bicúbicas de Bézier (Trabalho 1.9)

Uma superfície é uma lista de retalhos, e cada retalho é a sua matriz de geometria: 4×4 pontos de controle.
Cada ponto `Q(s,t) = S·M_B·G·M_Bᵀ·Tᵀ` é a soma das 16 *blending functions* `B_i(s)·B_j(t)` vezes os pontos
de controle, e o retalho é desenhado como uma grade de curvas (passo 0,1 em s e em t). Como tudo até agora,
o clipping é 2D, contra a window, depois da projeção.

Exemplo pronto para colar (*Add object* → tipo *surface*): o Dataset 1 do exercício "Plotagem de Superfície
Bézier Bicúbica", escalado por 0,2 e centrado — um retalho de 60×60 em z = 0 com uma elevação no meio:

```
(-30,-30,0),(-30,-10,0),(-30,10,0),(-30,30,0);(-10,-30,0),(-10,-10,20),(-10,10,20),(-10,30,0);(10,-30,0),(10,-10,20),(10,10,20),(10,30,0);(30,-30,0),(30,-10,0),(30,10,0),(30,30,0)
```

Roteiro rápido:

1. *Samples → 3D models → Bezier Surface*: um "terreno" ondulado de 3 retalhos lido de
   `samples/3d/bezier_surface.obj` — de frente aparece o perfil da onda.
2. Orbite com o botão esquerdo (ou *Window rotation* → *Pitch*, 30°): aparece a malha dos 3 retalhos, com
   junções suaves.
3. *Projection → Perspective* e o slider *COP distance d*: as partes mais próximas do COP crescem.
4. Zoom e pan até a superfície cruzar a borda vermelha: as linhas são cortadas na borda.
5. *Add object* → tipo *surface* → cole o exemplo acima e orbite: um retalho com a elevação no meio.
6. Com 15 pontos (ou 5 linhas) aparece o aviso *Invalid object* e nada é adicionado.
7. *File → Export .obj...* e depois *File → Import .obj...*: a mesma superfície volta (gravada com `surf`).

### Formato das coordenadas

Padrão exigido pela spec, aceito no campo *Coordinates*:

```
(x1, y1),(x2, y2),...
```

- **point** → exatamente 1 coordenada: `(0, 0)`
- **line** → exatamente 2 coordenadas: `(-10, 0),(10, 0)`
- **wireframe** → 2 ou mais; com 3+ o polígono é fechado automaticamente:
  `(-10,-10),(10,-10),(10,10),(-10,10)`

O parsing usa `list(eval(...))` (diretiva da spec), isolado em
[`src/persistence/parser.py`](../src/persistence/parser.py).

Desde o Trabalho 1.7 o mundo é 3D: todo tipo aceita `(x, y, z)`, e um `(x, y)` vale `(x, y, 0)`.

- **object3d** (modelo de arame) → pontos em **pares**, um segmento por par:
  `(0,0,0),(50,0,0),(0,0,0),(0,50,0),(0,0,0),(0,0,50)` (três arestas saindo da origem)
- **surface** (superfície bicúbica de Bézier, 1.9) → as **linhas** da matriz de geometria separadas por `;`,
  4 pontos por linha; cada 4 linhas (16 pontos) formam um retalho:
  `(x11,y11,z11),(x12,y12,z12),(x13,y13,z13),(x14,y14,z14);(x21,y21,z21),...;...`

## Rodar os testes

```bash
uv run pytest
```

Cobrem o núcleo geométrico sem precisar de GUI: `geometry`, `viewport` (incluindo a garantia de
**não-distorção**: quadrado continua quadrado), `display_file`/objetos e `parser`. A camada GUI é só
borda (PyQt) e não é coberta por testes automatizados.

## Notas de ambiente

- **Python:** o uv seleciona uma versão com wheels do PyQt6 disponíveis (atualmente 3.13). O código
  exige `>=3.11`.
- **Binding Qt:** usamos **PyQt6** (e não PyQt5) por ter wheels pré-compiladas mais atuais. Se algum dia
  for preciso trocar de binding, a mudança fica contida na camada `src/gui/` — o domínio não importa Qt.
- **Headless / CI:** para rodar a GUI sem display (só para checar import/render), use
  `QT_QPA_PLATFORM=offscreen uv run python src/main.py`.

## Estrutura executável

```
src/
  domain/        núcleo gráfico (Python puro, testável)
  persistence/   parsing de entrada (.obj virá no 1.3)
  app/           controller + render_pipeline (a espinha dorsal)
  gui/           PyQt6 (só as bordas)
  main.py        ponto de entrada
tests/           testes do núcleo
```

Detalhes de arquitetura e do plano 2D→3D: [`docs/design/trabalho-1.1-sketch.md`](design/trabalho-1.1-sketch.md).
