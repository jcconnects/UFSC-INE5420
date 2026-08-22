# Trabalho 1.3 - Implemente ao seu Sistema Gráfico Interativo a capacidade de realizar rotações na Window

Vencimento: segunda-feira, 14 set. 2026, 22:08

---

## Como implementar a rotação da window durante a navegação ?

- Considere a window como um objeto gráfico qualquer e aplique a rotação de objetos sobre um ponto arbitrário à window em WC.
- Recalcule as coordenadas do mundo em PPC aplicando o algoritmo Gerar Descrição em PPC
  - Observe que o mundo será girado na direção contrária àquela que você girou a window.

**Acrescente ao seu Sistema Gráfico Interativo a capacidade de realizar rotações na Window.** Para tal:

- Altere a representação dos objetos do mundo para suportar representação em um dos sistemas de coordenadas vistos em aula: Sistema de Coordenadas Normalizado (SCN) ou o Sistema de Coordenadas do Plano de Projeção (PPC). Agora a transformada de viewport é feita com estas coordenadas novas.
- Atualize a translação e o zoom da window tendo em vista o novo sistema de coordenadas. A translação em particular, tanto da window quanto dos objetos, deve levar em conta sempre o "para cima" do ponto de vista do usuário.
- Implemente a rotação implementando o algoritmo para gerar a descrição no sistema de coordenadas escolhido.
- Atualize a interface da aplicação para que o usuário possa rotacionar a window também. Como a rotação é sempre ao redor do centro da window, basta um campo para colocar o ângulo de rotação.
- Atenção: As coordenadas dos objetos não podem se modificar com a rotação da window, essa transformação ocorre ou na *cache* que seu display file possui ou na hora do desenho.

Cuidado para não "quebrar" as funcionalidades que já existiam! Por exemplo, o que acontece com uma translação de um objeto quando a window está rotacionada em um ângulo qualquer? Em geral, o que deve ocorrer com a inclusão de um novo objeto quando a window se encontra fora de sua orientação padrão?

## REQUISITOS ADICIONAIS:

O código entregue com este trabalho deve ser capaz de ler/escrever um mundo em formato **Wavefront .obj file**, devendo inluir todas as rotinas para leitura/escrita de arquivos .obj.

Sugestões de Modelagem:

- Crie uma classe DescritorOBJ capaz de transcrever um objeto gráfico para o formato .obj, tomando seu nome, seu tipo, seus vértices e suas arestas.
- Chame o descritor para cada objeto de seu mundo.
- Assim você só precisa se preocupar com o cabeçalho do .obj. O resto de se resove através de um percurso do display file com seu descritor.

## Funções equivalentes/semelhantes no Blender (2.91)

Na visão "Top Orthographic" (NumPad 7):

- Rotação da Window: Shift + NumPad 4 e Shift + NumPad 6
- Importar arquivo .obj: *File* > *Import* > *Wavefront (.obj)*
