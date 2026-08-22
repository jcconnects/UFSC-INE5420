# Trabalho 1.9 - Desenhando Superfícies Bicúbicas de Bézier

Vencimento: segunda-feira, 2 nov. 2026, 22:08

---

## Implemente o desenho em 3D de superfícies bicúbicas de Bézier.

**Objetivos de Aprendizagem:**

- Compreender como se constrói uma Função de Suavização para Superfícies Bicúbicas a partir de 16 pontos de controle;
- Compreender como se desenha uma superfície bicúbica a partir de seus pontos de controle;
- Compreender como se desenha uma superfície B-Spline composta a partir de "retalhos de superfície".

**Requisitos**:

- Estenda o seu sistema para representar superfícies 3D através de suas matrizes de geometria.
- Cada superfície pode ser representada por uma lista de matrizes, cada matriz representando um "retalho".
- Crie uma tela de entrada de dados onde você pode entrar com conjuntos de pontos de controle, 16 a 16, no mesmo padrão dos outros objetos com as linhas da matriz separadas por ";": (x_11,y_11,z_11),(x_12,y_12,z_12),...;(x_21,y_21,z_21),(x_22,y_22,z_22),...;...(x_ij,y_ij,z_ij)
- Carregue uma superfície composta por pelo menos 3 "retalhos" na forma de um arquivo .obj contendo os pontos de controle;
- Como tudo até agora, o clipping é em 2D.
