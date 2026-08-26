#!/usr/bin/env python3
"""Receive MJPEG stream from robot and save as video file. Run on PC."""

import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print('[ERROR] OpenCV required on PC for video recording')
    sys.exit(1)

DEFAULT_URL = 'http://192.168.4.1:8080'
DEFAULT_OUTPUT_DIR = Path('/home/arrma/Computer_vision_in_navigation_of_unmanned_robotic_systems/records')

JPEG_SOI = b'\xff\xd8'
JPEG_EOI = b'\xff\xd9'


def stream_frames(url=DEFAULT_URL, timeout=10):
    """Генератор кадров из MJPEG-потока с автопереподключением."""
    while True:
        try:
            req = urllib.request.urlopen(url, timeout=timeout)
        except Exception as e:
            print(f'[WARN] Cannot connect: {e}. Retry in 3s...')
            time.sleep(3)
            continue
        buf = b''
        try:
            while True:
                chunk = req.read(65536)
                if not chunk:
                    print('[WARN] Stream ended by server, reconnecting...')
                    break
                buf += chunk
                while True:
                    start = buf.find(JPEG_SOI)
                    end = buf.find(JPEG_EOI)
                    if start == -1 or end == -1 or end < start:
                        break
                    jpg = buf[start:end + 2]
                    buf = buf[end + 2:]
                    img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        yield img
        except Exception as e:
            print(f'[WARN] Stream lost: {e}. Reconnecting...')
        finally:
            req.close()
        time.sleep(1)


def main():
    URL = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    # If output file not specified, create timestamped filename in records dir
    if len(sys.argv) > 2:
        OUTPUT_FILE = Path(sys.argv[2])
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        OUTPUT_FILE = DEFAULT_OUTPUT_DIR / f'received_{timestamp}.avi'
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f'[INFO] Connecting to {URL} ...')
    print(f'[INFO] Recording to {OUTPUT_FILE}')

    writer = None
    frame_count = 0

    try:
        for img in stream_frames(URL):
            frame_count += 1

            if writer is None:
                h, w = img.shape[:2]
                frame_size = (w, h)
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                writer = cv2.VideoWriter(str(OUTPUT_FILE), fourcc, 30.0, frame_size)
                if not writer.isOpened():
                    print('[ERROR] Cannot open video writer')
                    return
                print(f'[INFO] Video writer opened: {frame_size[0]}x{frame_size[1]} @ 30fps (MJPG/AVI)')

            writer.write(img)

            cv2.imshow('Robot Stream (ESC/q to quit)', img)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                print(f'\n[INFO] Stopped by user. Saved {frame_count} frames.')
                return

            if frame_count % 30 == 0:
                print(f'[INFO] {frame_count} frames recorded...')

    except KeyboardInterrupt:
        print(f'\n[INFO] Interrupted. Saved {frame_count} frames to {OUTPUT_FILE}')
    finally:
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        print(f'[INFO] Done. Video saved: {str(OUTPUT_FILE)}')


if __name__ == '__main__':
    main()
