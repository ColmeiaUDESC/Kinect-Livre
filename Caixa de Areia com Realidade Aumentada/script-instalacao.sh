git clone https://github.com/ColmeiaUDESC/Kinect-Livre.git

cd Kinect-Livre/Caixa\ de\ Areia\ com\ Realidade\ Aumentada/1-instalacao/biblioteca

sudo dpkg -i libdc1394-22-dev_2.2.5-1_amd64.deb
sudo dpkg -i libdc1394-22_2.2.5-1_amd64.deb

cd ..
bash Build-Ubuntu-MOD.sh

cd ~/src
wget http://web.cs.ucdavis.edu/~okreylos/ResDev/Kinect/Kinect-3.10.tar.gz
tar -xfz Kinect-3.10.tar.gz
cd Kinect-3.10
make
sudo make install
sudo make installudevrules

cd ~/src/SARndbox-2.8
RawKinectViewer -compress 0