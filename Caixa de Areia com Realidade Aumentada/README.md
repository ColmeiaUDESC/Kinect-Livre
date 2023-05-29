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
- Computador Lenovo (ESPECIFICAR O COMPUTADOR)
- Kinect (ESPECIFICAR O KINECT)
- Projetor (NAO PRECISO NEM REPETIR NÉ)

## 🤓 Implementação
A implementação desse projeto sera dividída em duas etapas, com seus arquivos separados por pastas numeradas por passo: 
  1. Instalação dos softwares com ajustes nacessários para funcionar no nosso sistema
  2. Calibração com o projetor

### 1 - Instalação
#### 1.1 - Sistema Operacional
> Idealmente é para usar o Linux Mint 19.3 ("Tricia") com MATE DE, mas por ser uma versão muito datada ele não instalava no nosso notebook

- Instale [Linux Mint 21.1 "Vera" com MATE DE](https://linuxmint.com/edition.php?id=303) (Backup da ISO em `Caixa de Areia com Realidade Aumentada/1-instalacao/iso`).
> _IMPORTANTE NÃO ATUALIZAR O SISTEMA DEPOIS DE INSTALAR_.

- Durante a instalação deve aceitar a opção de Softwares de Terceiros para os drivers de video funcionarem direito.
- Depois de instalar tudo tem que settar os drivers de video se eles não funcionarem automaticamente.

#### 1.2 - Biblioteca desatualizada
> Necessário manualmente instalar libdc1394-22 e libdc1394-22-dev

- Baixe os dois arquivos .deb em `Caixa de Areia com Realidade Aumentada/1-instalacao/biblioteca`
- Instale primeiro o `libdc1394-22` e depois `libdc1394-22-dev`

#### 1.3 - Instalando Vrui
> Vrui normal tem um problema com o compilador então eu feiz uma modificaçao nele.

- Baixe o `Vrui-8.0-002-MOD.tar.gz` de `Caixa de Areia com Realidade Aumentada/1-instalacao/vrui`
- Mova para o arquivo para mas não extraia `~/`
- Baixe o `Build-Ubuntu-MOD.sh` de `Caixa de Areia com Realidade Aumentada/1-instalacao/scrip`
- Execute o script: 
```bash
bash Build-Ubuntu-MOD.sh`
```
- SE TUDO DEU CERTO EU SOU FODA E SOU O GENIO DO BASH
- Pode deletar o script: 
```bash
cd ~
rm Build-Ubuntu-MOD.sh`
```

#### 1.4 - Kinect Drivers
```bash
cd ~/src
wget http://web.cs.ucdavis.edu/~okreylos/ResDev/Kinect/Kinect-3.10.tar.gz
tar xfz Kinect-3.10.tar.gz
cd Kinect-3.10
make
sudo make install
sudo make installudevrules
ls /usr/local/bin
```

