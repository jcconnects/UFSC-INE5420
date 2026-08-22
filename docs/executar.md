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
[`src/persistence/parser.py`](../src/persistence/parser.py). O formato já aceita a 3ª coordenada
`(x, y, z)` prevista para o Trabalho 1.7 (3D).

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
