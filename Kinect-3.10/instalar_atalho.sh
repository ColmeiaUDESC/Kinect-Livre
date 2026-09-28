#!/bin/sh
# Cria o atalho do painel com os caminhos desta cópia do projeto.
# Uso: ./instalar_atalho.sh
# Para fixar outra instalação do SARndbox no atalho:
#   SARNDBOX_DIR=/caminho/para/SARndbox-2.8 ./instalar_atalho.sh
set -e

DIR=$(cd "$(dirname "$0")" && pwd -P)
NAME="Painel da Caixa de Areia.desktop"
PYTHON=$(command -v python3 || echo /usr/bin/python3)

ICON=applications-science
for candidate in "$DIR/../colmeia.jpg" "$DIR/colmeia.jpg"; do
    if [ -f "$candidate" ]; then
        ICON=$(cd "$(dirname "$candidate")" && pwd -P)/colmeia.jpg
        break
    fi
done

EXEC="\"$PYTHON\" \"$DIR/regular_altura.py\""
if [ -n "$SARNDBOX_DIR" ]; then
    EXEC="env \"SARNDBOX_DIR=$SARNDBOX_DIR\" $EXEC"
fi

APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS"
cat > "$APPS/$NAME" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Painel da Caixa de Areia
Comment=Ajustar alturas, área do Kinect e projeção pelo painel
Exec=$EXEC
Path=$DIR
Icon=$ICON
Terminal=false
Categories=Education;Science;
EOF
chmod +x "$APPS/$NAME"
echo "Atalho criado no menu de aplicativos: $APPS/$NAME"

DESKTOP=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
if [ -d "$DESKTOP" ]; then
    if [ -e "$DESKTOP/$NAME" ]; then
        echo "Já existe um atalho em $DESKTOP; ele não foi alterado."
    else
        cp "$APPS/$NAME" "$DESKTOP/$NAME"
        chmod +x "$DESKTOP/$NAME"
        # No Ubuntu, o atalho só abre com um clique depois de marcado como confiável.
        gio set "$DESKTOP/$NAME" metadata::trusted true 2>/dev/null || true
        echo "Atalho criado na área de trabalho: $DESKTOP/$NAME"
    fi
fi
