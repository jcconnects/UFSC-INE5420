"""Trabalho 1.4.3 -- B-Spline cúbica uniforme desenhada por Diferenças Adiante.

Enunciado (`1.4.3 - Prática manual de B-Spline utilizando Foward Differnences.md`):
    "Pegue os mesmos dados (pontos) do exercício das curvas de Bézier.
     Use-os para plotar 1 curva B-Spline baseada em 10 pontos de controle.
     Use Forward Differences."

Uma B-Spline cúbica uniforme sobre N pontos de controle tem N-3 segmentos, cada
um definido por uma janela deslizante de 4 pontos consecutivos. Para os 10 pontos
dados são 7 segmentos (P1-P4, P2-P5, ..., P7-P10). (O enunciado cita "3 sub-curvas
/ 3 matrizes δ"; isso é resíduo -- a contagem correta para 10 pontos de controle é
7, e o estado δ / de condições iniciais abaixo é gerado para cada um dos 7.)

Por segmento, com a janela G = [Pi, Pi+1, Pi+2, Pi+3] e t em [0, 1]:

              [ -1   3  -3   1 ]
    M_BS = 1/6 [  3  -6   3   0 ]      C(t) = T . M_BS . G ,  T = [t^3 t^2 t 1]
              [ -3   0   3   0 ]
              [  1   4   1   0 ]

Os coeficientes [a, b, c, d] = M_BS . G (calculados por eixo) dão C(t) = a t^3 +
b t^2 + c t + d. As Diferenças Adiante avaliam essa cúbica só com somas: em vez de
recalcular T . M_BS . G a cada t, guardamos o estado de diferenças [f, Δf, Δ²f,
Δ³f] e o avançamos n vezes. Δ = 1/n (o passo), e as condições iniciais (as "C.I."
que o enunciado pede) são

    f0  = d
    Δf  = a Δ³ + b Δ² + c Δ
    Δ²f = 6 a Δ³ + 2 b Δ²
    Δ³f = 6 a Δ³

A atualização por Diferenças Adiante (δ / E) é então, repetida n vezes:

    f += Δf ;  Δf += Δ²f ;  Δ²f += Δ³f

Execução:  python3 "1.4.3 - Prática manual de B-Spline em Sala de Aula utilizando Foward Differences.py"
Requer numpy + matplotlib (pip install numpy matplotlib). Em máquina sem tela,
troque plt.show() por plt.savefig("bspline.png") no final.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

# Os 10 pontos de controle, idênticos aos do exercício de Bézier:
# P1(1,1) P2(2,3) P3(3,0) P4(4,1) P5(5,2) P6(4,4) P7(6,4) P8(7,4) P9(6,2) P10(7,1)
CONTROL_POINTS = np.array(
    [
        [1.0, 1.0],
        [2.0, 3.0],
        [3.0, 0.0],
        [4.0, 1.0],
        [5.0, 2.0],
        [4.0, 4.0],
        [6.0, 4.0],
        [7.0, 4.0],
        [6.0, 2.0],
        [7.0, 1.0],
    ]
)

# Matriz base da B-Spline cúbica uniforme M_BS. As linhas multiplicam a base de
# potências T = [t^3, t^2, t, 1]; as colunas ponderam os quatro pontos da janela.
M_BS = (1.0 / 6.0) * np.array(
    [
        [-1.0, 3.0, -3.0, 1.0],
        [3.0, -6.0, 3.0, 0.0],
        [-3.0, 0.0, 3.0, 0.0],
        [1.0, 4.0, 1.0, 0.0],
    ]
)

POINTS_PER_SEGMENT = 4  # um segmento cúbico abrange 4 pontos de controle consecutivos


def forward_difference_setup(coeffs: np.ndarray, delta: float) -> np.ndarray:
    """Estado inicial de diferenças [f, Δf, Δ²f, Δ³f] de uma coordenada cúbica.

    `coeffs` é [a, b, c, d] com C(t) = a t^3 + b t^2 + c t + d; `delta` é o passo
    1/n. Esses quatro números são as "condições iniciais" (C.I.) que o laço de
    Diferenças Adiante avança. O mapeamento de coeffs para esse estado é ele
    próprio uma matriz (a matriz δ a que o enunciado se refere):

        [ f  ]   [ 0    0    0   1 ] [ a ]
        [ Δf ] = [ Δ³   Δ²   Δ   0 ] [ b ]
        [ Δ²f]   [ 6Δ³  2Δ²  0   0 ] [ c ]
        [ Δ³f]   [ 6Δ³  0    0   0 ] [ d ]
    """
    a, b, c, d = coeffs
    d1 = delta
    d2 = delta * delta
    d3 = d2 * delta
    return np.array(
        [
            d,
            a * d3 + b * d2 + c * d1,
            6.0 * a * d3 + 2.0 * b * d2,
            6.0 * a * d3,
        ]
    )


def sample_segment(window: np.ndarray, n: int, verbose: bool = False) -> np.ndarray:
    """Amostra um segmento da B-Spline em n+1 pontos usando Diferenças Adiante.

    `window` é o bloco (4, 2) de pontos de controle [Pi..Pi+3]. Retorna um vetor
    (n+1, 2) de pontos, de t=0 a t=1 inclusive.
    """
    delta = 1.0 / n
    # Coeficientes por eixo: coeffs[:, 0] = cúbica em x, coeffs[:, 1] = cúbica em y.
    coeffs = M_BS @ window  # forma (4, 2): linhas [a; b; c; d]
    state_x = forward_difference_setup(coeffs[:, 0], delta)
    state_y = forward_difference_setup(coeffs[:, 1], delta)

    if verbose:
        print(f"    coeficientes [a,b,c,d] x: {coeffs[:, 0]}")
        print(f"    coeficientes [a,b,c,d] y: {coeffs[:, 1]}")
        print(f"    C.I. [f,Δf,Δ²f,Δ³f] x: {state_x}")
        print(f"    C.I. [f,Δf,Δ²f,Δ³f] y: {state_y}")

    points = np.empty((n + 1, 2))
    fx, dfx, d2fx, d3fx = state_x
    fy, dfy, d2fy, d3fy = state_y
    for step in range(n + 1):
        points[step] = (fx, fy)
        # Atualização por Diferenças Adiante (só somas -- a essência do método).
        fx += dfx; dfx += d2fx; d2fx += d3fx
        fy += dfy; dfy += d2fy; d2fy += d3fy
    return points


def sample_bspline(points: np.ndarray, n: int, verbose: bool = False) -> np.ndarray:
    """Amostra a B-Spline cúbica uniforme inteira em uma única polilinha.

    Percorre as N-3 janelas deslizantes. Segmentos consecutivos se encontram numa
    junção compartilhada, então todo segmento depois do primeiro descarta seu
    ponto em t=0 para evitar duplicação (espelha o descarte de junção em
    src/domain/curves.py::sample_curve).
    """
    segment_count = len(points) - (POINTS_PER_SEGMENT - 1)
    if segment_count < 1:
        raise ValueError(
            f"são necessários ao menos {POINTS_PER_SEGMENT} pontos de controle; "
            f"recebidos {len(points)}"
        )

    pieces: list[np.ndarray] = []
    for i in range(segment_count):
        if verbose:
            print(f"  segmento {i} -> pontos de controle P{i + 1}..P{i + 4}")
        window = points[i : i + POINTS_PER_SEGMENT]
        segment = sample_segment(window, n, verbose=verbose)
        # O primeiro segmento emite seu início; os demais o pulam (junção compartilhada).
        pieces.append(segment if i == 0 else segment[1:])
    return np.vstack(pieces)


def _direct_point(window: np.ndarray, t: float) -> np.ndarray:
    """C(t) = T . M_BS . G de um segmento, avaliada diretamente (sem diferenças).

    Implementação de referência usada apenas para conferir o resultado das
    Diferenças Adiante.
    """
    power = np.array([t * t * t, t * t, t, 1.0])
    return power @ M_BS @ window


def _self_check(n: int) -> None:
    """Verifica que as Diferenças Adiante batem com a avaliação direta T.M_BS.G."""
    window = CONTROL_POINTS[0:POINTS_PER_SEGMENT]
    fd = sample_segment(window, n)
    for step in range(n + 1):
        direct = _direct_point(window, step / n)
        assert np.allclose(fd[step], direct, atol=1e-9), (
            f"divergência das Diferenças Adiante no passo {step}: {fd[step]} != {direct}"
        )
    print(f"[verificação] Diferenças Adiante batem com T.M_BS.G em todos os {n + 1} "
          "passos do segmento 0 (tol 1e-9). OK")


def plot(control_points: np.ndarray, curve: np.ndarray) -> None:
    """Desenha a curva B-Spline, seu polígono de controle e os pontos rotulados."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(
        control_points[:, 0], control_points[:, 1],
        linestyle="--", color="0.7", marker="o", markersize=5,
        label="polígono de controle",
    )
    ax.plot(curve[:, 0], curve[:, 1], color="tab:blue", linewidth=2, label="B-Spline")
    for index, (x, y) in enumerate(control_points, start=1):
        ax.annotate(f"P{index}", (x, y), textcoords="offset points", xytext=(6, 4))

    ax.set_title("B-Spline cúbica uniforme por Diferenças Adiante (7 segmentos)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    SUBDIVISIONS = 30  # n: pontos por segmento = n + 1

    print("Preparação das Diferenças Adiante por segmento (matrizes δ / C.I.):")
    curve = sample_bspline(CONTROL_POINTS, SUBDIVISIONS, verbose=True)
    print(f"\nGerados {len(curve)} pontos em "
          f"{len(CONTROL_POINTS) - (POINTS_PER_SEGMENT - 1)} segmentos.")

    _self_check(SUBDIVISIONS)

    # Uma B-Spline uniforme NÃO interpola seus extremos. Em t=0 a linha da base é
    # [1, 4, 1, 0]/6, então a curva começa em (P1 + 4 P2 + P3) / 6, não em P1.
    p1, p2, p3 = CONTROL_POINTS[0], CONTROL_POINTS[1], CONTROL_POINTS[2]
    expected_start = (p1 + 4.0 * p2 + p3) / 6.0
    assert np.allclose(curve[0], expected_start, atol=1e-9)
    print(f"[nota] início da curva {curve[0]} = (P1 + 4 P2 + P3)/6 {expected_start} "
          "(a B-Spline não passa por P1)")

    plot(CONTROL_POINTS, curve)
