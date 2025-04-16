if [ "$EUID" -ne 0 ]
  then echo "Por favor, execute como root (sudo script-instalacao.sh)"
  exit
fi
USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
git clone https://github.com/ColmeiaUDESC/Kinect-Livre.git

cd Kinect-Livre/Caixa\ de\ Areia\ com\ Realidade\ Aumentada/arquivos/biblioteca

sudo dpkg -i libdc1394-22-dev_2.2.5-1_amd64.deb
sudo dpkg -i libdc1394-22_2.2.5-1_amd64.deb

cd ..
bash Build-Ubuntu-MOD.sh

cd $USER_HOME/src
wget http://web.cs.ucdavis.edu/~okreylos/ResDev/Kinect/Kinect-3.10.tar.gz
tar -xfz Kinect-3.10.tar.gz
cd Kinect-3.10
make
sudo make install
sudo make installudevrules

cd $USER_HOME/src
curl -L "https://avatars.githubusercontent.com/u/54866625?s=400&u=184d63b6c7ecc161f9ebbad8f6e7b32b2e600253&v=4" -o colmeia.jpg
cd SARndbox-2.8
touch RunSARndbox.sh
printf "#!/bin/bash\n
cd ~/src/SARndbox-2.8\n
./bin/SARndbox -uhm -fpv" >> RunSARndbox.sh

chmod a+x $USER_HOME/src/SARndbox-2.8/RunSARndbox.sh
cd ~/Desktop/
touch Caixa\ de\ Areia.desktop
printf "
[Desktop Entry]
Version=1.0
Type=Application
Terminal=false
Icon=~/src/colmeia.png
Exec=~/src/SARndbox-2.8/RunSARndbox.sh
Name=Começa a Caixa de Areia
Comment=" >> 