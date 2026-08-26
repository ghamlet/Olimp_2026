#!/usr/bin/env bash
# Синхронизация файлов с ноутбуком на робота по rsync/ssh.
# Использование:
#   ./sync_to_robot.sh             — разовая синхронизация
#   ./sync_to_robot.sh --dry-run   — показать, что изменится, без копирования
#   ./sync_to_robot.sh --watch     — непрерывная синхронизация при изменении файлов
set -euo pipefail

LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_USER="pi"
REMOTE_HOST="192.168.4.1"
REMOTE_DIR="/home/pi/base"

EXCLUDES=(
    --exclude='__pycache__/'
    --exclude='*.pyc'
    --exclude='.git/'
    --exclude='*.md'
    --exclude='records/'
)

RSYNC_SSH="ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new"

sync_once() {
    rsync -av "${EXCLUDES[@]}" -e "$RSYNC_SSH" \
        "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
}

dry_run() {
    rsync -avn "${EXCLUDES[@]}" -e "$RSYNC_SSH" \
        "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
}

watch() {
    sync_once
    echo "[INFO] Watching $LOCAL_DIR for changes (Ctrl+C to stop)..."
    if command -v inotifywait >/dev/null 2>&1; then
        while true; do
            inotifywait -q -r -t 30 -e modify,create,close_write,delete,move \
                --exclude '__pycache__|\.pyc' "$LOCAL_DIR" >/dev/null 2>&1 || true
            sleep 0.3
            sync_once || true
        done
    else
        echo "[INFO] inotify-tools не установлены, опрос каждые 2 секунды"
        while true; do
            sleep 2
            sync_once || true
        done
    fi
}

case "${1:-}" in
    --watch|-w)
        watch
        ;;
    --dry-run|-n)
        dry_run
        ;;
    *)
        sync_once
        ;;
esac
