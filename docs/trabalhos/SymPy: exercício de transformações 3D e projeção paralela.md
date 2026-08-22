# SymPy: exercício de transformações 3D e projeção paralela

---

Implemente utilizando a biblioteca SymPy em um Jupyter notebook um conjunto de células de código que execute as seguintes operações objetivando a projeção paralela de um paralelepípedo situado em um ângulo oblíquo à frente de uma Window em um sistema de coordenadas tridimensional

## Dados da Window

- Window Center nas coordenadas 10,10,0
- Dimensão horizontal da Window 16 unidades
- Dimensão vertical da Windows 10 unidades
- Window alinhada com o plano XY

## Dados do paralelepípedo

- Lado menor 4 unidades
- Lado maior 12 unidades
- Centro geométrico nas coordenadas 10,10,20
- Rotação em torno do eixo Y de 45 graus
- Rotação em torno do eixo X de 30 grau

## Ações a serem realizadas

Crie variáveis contendo as estruturas de dados representando tanto a Windows quanto o paralelepípedo

- Rotacione o paralelepípedo em 3D de forma a que ele satisfaça as duas condições de rotação acima e que ao final o seu centro geométrico esteja na posição 10,10,20
- Execute a projeção paralela do paralelepípedo sobre a Window, clipando caso necessário (Não há necessidade de transformar para coordenadas normalizadas, você pode realizar o clipe diretamente em coordenadas do mundo neste caso aqui)
- Faça uma representação gráfica do resultado mostrando os limites da Window e o desenho resultante do paralelepípedo projetado

Da mesma forma que o exercício anterior em SymPy, toda a equipe que entregar um exemplar funcionando e com os resultados corretos (em .ypnb) terá direito a ganhar um ponto a mais em qualquer um dos 10 pequenos trabalhos do primeiro módulo.
