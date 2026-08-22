# Trabalho 1.5 - Implemente Curvas em 2D usando Blending Functions (novo)

Vencimento: segunda-feira, 28 set. 2026, 22:08

---

**Implemente a curva de Hermite ou Bézier como mais um objeto gráfico de seu sistema:**

- Um objeto Curva2D poderá conter uma ou mais curvas com continuidade no mínimo G(0).
- Crie uma interface para entrar com estes dados no padrão `(x1,y1),(x2,y2),...` Deve ser possível informar um número infinito de pontos para implementar continuidade.
- Implemente o Clipping para esta curva utilizando o método descrito em aula (e nas transparências).

## Funções equivalentes/semelhantes no Blender (2.91)

Na visão "Top Orthographic" (`NumPad 7`):

- **Adicionar curva de Bezier:** `Shift + A` > *Curve* > *Bezier*.
- **Continuidade:** Selecionar Curva > `Tab` (Para entrar em modo de edição) > Selecionar vértice > `E` (Extrude)
