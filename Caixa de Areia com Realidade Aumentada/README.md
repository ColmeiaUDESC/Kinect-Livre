<p align="center">
    <img src="https://avatars.githubusercontent.com/u/54866625?s=400&u=184d63b6c7ecc161f9ebbad8f6e7b32b2e600253&v=4" alt="Logo" width="160" height="160">
  </a>
  <h1 align="center">Caixa de Areia com Realidade Aumentada</h1>
</p>

## 🤔 O que é?
Projeção do relevo de uma caixa contendo areia em tempo real com simulação de fluidos nesse relevo. Feito utilizando um Kinect posicionado ortogonalmente acima da caixa e ao seu lado um projetor, ambos apontando para a areia dessa caixa. 

## 🫥 Inspiração
A ideia inicial surgiu ao assistir vídeos curtos sobre projetos semelhantes em redes sociais. Após pesquisas, decidimos implementar o trabalho desenvolvido por UC Davis' W.M. Keck Center for Active Visualization in the Earth Sciences (KeckCAVES), UC Davis Tahoe Environmental Research Center, Lawrence Hall of Science,  ECHO Lake Aquarium and Science Center. 
É possível encontar o projeto original no [site oficial](https://web.cs.ucdavis.edu/~okreylos/ResDev/SARndbox/) do Oliver Kreylos, junto com mais informações relacionadas a origem do projeto e aprofundamento no tutorial de instalação.

## 🎒 Materiais
- Computador (Recomendado um computador de mesa com placa de vídeo GeForce GTX 1060, processador Intel Core i5 e 4GB de RAM. Não é um programa muito pesado, em termos de computadores atuais.)
- Kinect 1, modelo usado no Xbox 360 (tanto faz o 1414, 1473 ou o Kinect for Windows)
- Projetor de tela, preferencialmente com resolução nativa de 4:3
- Caixa retangular com proporção 4:3.
- Suporte para o Kinect e projetor. Importante o suporte deixar o Kinect e o projetor acima e no meio da caixa, apontados para ela.
- Areia tratada 

## 🤓 Implementação
A implementação desse projeto sera dividída em duas etapas, com seus arquivos separados por pastas numeradas por passo: 
  1. Instalação dos softwares com ajustes necessários para funcionar no nosso sistema
  2. Calibração com o projetor

### 1 - Instalação
#### 1.1 - Sistema Operacional
> Idealmente é para usar o Linux Mint 19.3 ("Tricia") com MATE DE, mas por ser uma versão muito datada ele não instalava no nosso notebook. Testamos com o Ubuntu 24.04 e funcionou perfeitamente, mas não garantimos que funcione em versões futuras.

- Instale [Linux Mint 21.1 "Vera" com MATE DE](https://linuxmint.com/edition.php?id=303) (Backup da ISO em `Caixa de Areia com Realidade Aumentada/1-instalacao/iso`).
> _IMPORTANTE NÃO ATUALIZAR O SISTEMA DEPOIS DE INSTALAR_.

- Durante a instalação deve aceitar a opção de Softwares de Terceiros para os drivers de video funcionarem direito.
- Depois de instalar tudo tem que settar os drivers de video se eles não funcionarem automaticamente.

#### 1.2 - Rodar o script de instalação
- Nesse mesmo repositório, temos o arquivo `script-instalação.sh`. Baixe ele e execute.

#### 1.3 - Calibre o Kinect
- Com o Kinect já acima da caixa, execute `RawKinectViewer -o` no terminal do computador.
- Verifique se a câmera está alinhada com a caixa.
- Aperte o botão direito do seu mouse e selecione `average frames`.
- Aperte o botão `1` no seu teclado e selecione `Extract Planes`. Depois, coloque o mouse em um dos cantos da caixa, aperte e segure `1`, arraste até o outro canto da caixa e solte `1`
- Aperte o botão `2` no seu teclado e selecione `Measure 3D points`. E aperte o botão `2` nos cantos da caixa, seguindo essa ordem: Canto inferior esquerdo, canto inferior direito, canto superior esquerdo, canto superior direito.
- Veja no terminal que você executou o programa se tem algo parecido com:
```
Camera-space plane equation: x * (0.00532502, -0.0501786, 0.998726) = -115.296
(            -46.3606,             -37.7409,             -117.027)
(             32.4776,              -35.279,             -117.351)
(             -47.265,               39.513,             -112.917)
(             28.5548,              41.5887,             -113.528) 
```
- Copie as linhas anteriores e cole no arquivo de texto em `home/<usuario>/src/SARndbox-2.8/etc/SARndbox-2.8/BoxLayout.txt`
- Apague o texto antes do primeiro parenteses na primeira linha, e troque o sinal de igual por uma vírgula. No fim deve parecer com:
```
   (0.00532502, -0.0501786, 0.998726), -115.296
(            -46.3606,             -37.7409,             -117.027)
(             32.4776,              -35.279,             -117.351)
(             -47.265,               39.513,             -112.917)
(             28.5548,              41.5887,             -113.528) 
```
- Salve o documento, feche ele e o `RawKinectViewer`

#### 1.4 - Usando a caixa
- O relevo da caixa muda em tempo real. Tente mexer na areia e veja o mapa mudando!
- Para usar a caixa, basta clicar no ícone da área de trabalho (ou menu de aplicativos) com a logo do Colmeia.
- Para fazer chover em um ponto, abra bem a mão em cima da caixa. Numa altura um pouco maior que a caixa. E não tão perto da câmera.
- Para chover na caixa inteira, aperte o botão `1` no teclado.
- Para tirar a chuva, aperte o botão `2` no teclado.
- Para fechar o sistema, aperte o botão `Esc` no teclado.