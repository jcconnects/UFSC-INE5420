# 2026-08-13

Mundo pode ser infinito e a window escolhe qual parte do mundo eu vou mostrar.

- Tudo que está na window é o que eu estou enxergando
- Viewport é a área de tela que vou utilizar para desenhar.

Window e viewport são representados por estrutura de dados distintas.

---

Nosso sistema vai ter que ter a funcionalidade zoom e pan
Sistema precisa representar:

- Pontos
- Retas
- Polígonos (listas de pontos interconectados)

---

Decisão de projeto: iremos utilizar Qt para fazer o projeto, pois é mais utilizado na industria quando comparado com o TKinter

# 2026-08-18 - Aula 3 - Tranformações 2D e o Sistema de Coordenadas Homogêneo

Em 2D tudo pode ser feito a partir da combinação de 3 transformações base.

## Translação 2D

Mover um objeto em uma **quantidade de deslocamento**.
Objeto muda de posição.
Dx e Dy são os vetores de deslocamento do objeto.

x' = x + Dx
y' = y + Dy

## Escalonamento 2D

Aplicar um fator de escala em um objeto.
O objeto muda de tamanho.

## Rotação 2D

O objeto é rotacionado.

x' = x _ cos(0) - y _ sen(0)
y' = x _ sen(0) - y _ cos(0)

---

Tudo se resume a multiplicação de matrizes com um novo eixo W = 1.
Para cada transformação, uma matriz diferente é multiplicada pela matriz que representa o vetor originalmente.

Para o trabalho, só vou ter uma rotina de operação. A operação pode ser translação, escalonamento, rotação (em torno do centro do mundo, centro do objeto e em torno de um ponto qualquer)
