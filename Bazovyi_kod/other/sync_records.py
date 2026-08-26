import argparse
import subprocess
import time
from pathlib import Path

REMOTE_HOST = 'pi@192.168.4.1'
REMOTE_DIR = '/home/pi/base/records'
LOCAL_DIR = Path(__file__).resolve().parent / 'records'


def sync_once(verbose=False):
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        'rsync', '-avi', '--progress', '--ignore-existing',
        f'{REMOTE_HOST}:{REMOTE_DIR}/',
        str(LOCAL_DIR) + '/',
    ]
    if verbose:
        print(f'[*] rsync: {" ".join(cmd)}')
    result = subprocess.run(cmd)
    return result.returncode == 0


def sync_watch(interval, verbose=False):
    print(f'[*] Watch mode: проверка каждые {interval} сек. Ctrl+C для остановки.')
    while True:
        sync_once(verbose)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Синхронизация записей видео с Pi')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--once', action='store_true',
                       help='Скачать новые видео и выйти')
    group.add_argument('--watch', action='store_true',
                       help='Скачивать новые видео, пока скрипт активен')
    parser.add_argument('--interval', type=int, default=30,
                        help='Интервал проверки в секундах (по умолчанию 30, только для --watch)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Показать вывод rsync')
    args = parser.parse_args()

    try:
        if args.once:
            sync_once(args.verbose)
            print('[*] Готово.')
        elif args.watch:
            sync_watch(args.interval, args.verbose)
    except KeyboardInterrupt:
        print('\n[*] Остановлено.')


if __name__ == '__main__':
    main()
