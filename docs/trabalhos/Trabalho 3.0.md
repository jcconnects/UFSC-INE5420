# Trabalho 3.0 - Pixel Shading

Vencimento: domingo, 20 dez. 2026, 09:41

---

## **Trabalho 3: NOS SEMESTRES EM QUE FOR ESTENDIDO O SGI:**

- Trabalho 2.1.Rasterização sem checagem de profundidade no SGI: Implementação de framebuffer com as funções de limpar o buffer, desenhar pixel, desenhar linha, desenha trapézio alinhado, desenhar polígono e integração no SGI.
- Trabalho 2.2. Implementação do Z-buffer no Sistema Gráfico Interativo, após implementação da rasterização. Implementação de desenho de triângulo, implementação de checagem de profundidade. Obs: Não esqueça de considerar o buffer de profundidade na função de limpeza.
- Trabalho 2.3. Implementação de Iluminação de Phong no Sistema Gráfico Interativo após a implementação da resterização e do Z-buffer. Implementação de iluminação de phong.

Dica: Utilize o modelo da powergirl embutível em código (tópico "Modelo embutível em Código Fonte") para testar sua iluminação.

## Trabalho 2: NOS SEMESTRES EM QUE USARMOS O SHADER MAKER EM GPU:

Programe os algorítmos de iluminação no processador gráfico através de shaders. Será usado o ambiente [Shader Maker](http://cg.in.tu-clausthal.de/publications.shtml#shader_maker) para carregar os shaders, a cena e os parâmetros de iluminação. A cor do objeto deve ser definida pela soma das componentes ambiente, difusa e especular. Os algorítmos calculam as componentes difusas e especular, mas não necessariamente ambos. No caso dos algorítmos escolhidos calcularem a mesma componente, deve-se usar uma variável do tipo "uniform" para escolha em tempo de execução de qual algorítmo usar. O código com todos os algorítmos deve estar em um único par de arquivos (um arquivo para o Vertex Shader e outro para o Fragment Shader). Escolha pelo menos um dos algoritmos disponíveis nos slides.
