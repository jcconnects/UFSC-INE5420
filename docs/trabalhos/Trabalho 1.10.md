# Trabalho 1.10. Implementação de Superfícies Bicúbicas utilizando Diferenças Adiante

Vencimento: segunda-feira, 9 nov. 2026, 22:08

---

Implemente em seu SGI superfícies bicúbicas b-spline utilizando o Método das Diferenças Adiante (Forward Differences) para a geração do desenho.

**Requisitos:**

- Valem todos os requisitos já definidos paras as superfícies bicúbicas utilizando funções de suavização, no trabalho anterior.
- O usuário poderá entrar com qualquer matriz de pontos de controle entre dimensão 4x4 até dimensão 20x20, no padrão (x_11,y_11,z_11),(x_12,y_12,z_12),...;(x_21,y_21,z_21),(x_22,y_22,z_22),...;...(x_ij,y_ij,z_ij)
- O SGI automaticamente fará a subdivisão em submatrizes, que serão desenhadas pelo método das forward differences conforme explicado em sala de aula. Você pode utilizar o código-exemplo em Processing disponibilizado pelo Porfessor para se basear, lembrando que o algoritmo fornecido por Foley & van Dam possui dois erros (explicados pelo professor).
- A última versão do trabalho do primeiro módulo da disciplina deve poder abrir OBJ. Veja: http://en.wikipedia.org/wiki/Wavefront_.obj_file Na avaliação a inserção de objetos será através de arquivos deste tipo!

## Funções equivalentes/semelhantes no Blender (2.91)

Na visão "Top Orthographic" (NumPad 7):

- Adicionar superfície NURBS (tipo de superfície B-Spline): Shift + A > Surface > NURBS Surface
