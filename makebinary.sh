#!/bin/sh

pyinstaller --onefile --noconfirm --noconsole --clean --log-level=WARN --strip --hidden-import sklearn.neighbors.typedefs bin/graphshingling
