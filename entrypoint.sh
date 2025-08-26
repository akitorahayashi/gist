#!/bin/sh

# このスクリプトは、コンテナのCMDとして渡されたコマンドを実行します。
# exec "$@" を使用することで、渡されたコマンドがコンテナのPID 1として実行され、
# シグナル（例: docker stopからのSIGTERM）を正しく受信できるようになります。

set -eu

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start the main process
exec "$@"
