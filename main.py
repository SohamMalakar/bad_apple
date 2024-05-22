#!/usr/bin/env python3

import sys
import cv2
import time
import threading

from numba import njit
from moviepy.editor import VideoFileClip

res = 80
density = " .,-~:;=!*#$@"


def play_audio(video_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.preview()
    video.close()


@njit(parallel=True)
def generate_frame(width, height, grayscale):
    output = []
    for i in range(height):
        for j in range(width):
            index = int(grayscale[i, j] / 255 * (len(density) - 1))
            output.append(density[index])
        output.append("\n")
    return output


def build_cache(cap, width, height):
    cache = []
    print("Caching...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (width, height))
        grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        output = generate_frame(width, height, grayscale)
        cache.append("".join(output))

    return cache


def play_cached_video(cache, frame_duration):
    for frame in cache:
        start_time = time.time()
        print("\033[H\033[J", end="")
        print(frame)
        elapsed_time = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed_time)
        time.sleep(sleep_time)


def play_video(cap, width, height, frame_duration):
    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (width, height))
        grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        print("\033[H\033[J", end="")

        output = []
        for i in range(height):
            for j in range(width):
                index = int(grayscale[i, j] / 255 * (len(density) - 1))
                output.append(density[index])
            output.append("\n")

        print("".join(output))

        elapsed_time = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed_time)
        time.sleep(sleep_time)


def get_elapsed_time(cap, width, height):
    start_time = time.time()
    _, frame = cap.read()

    resized = cv2.resize(frame, (width, height))
    grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    output = []
    for i in range(height):
        for j in range(width):
            index = int(grayscale[i, j] / 255 * (len(density) - 1))
            output.append(density[index])
        output.append("\n")

    print("".join(output))

    elapsed_time = time.time() - start_time
    return elapsed_time


def main(argv):
    if len(argv) != 2 and len(argv) != 3:
        print(f"usage: {argv[0]} <video> [res]")
        exit(1)

    global res

    if len(argv) == 3:
        res = int(argv[2])

    cap = cv2.VideoCapture(argv[1])

    if not cap.isOpened():
        print(f"Error: Cannot open video {argv[1]}")
        exit(1)

    xh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    xw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    width = res
    height = int(width / xw * xh / 2)

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps

    elapsed_time = get_elapsed_time(cap, width, height)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if elapsed_time > frame_duration:
        print("\033[H\033[J", end="")
        cache = build_cache(cap, width, height)

        thread1 = threading.Thread(target=play_audio, args=(argv[1],))
        thread1.start()

        thread2 = threading.Thread(
            target=play_cached_video, args=(cache, frame_duration))
        thread2.start()
    else:
        thread1 = threading.Thread(target=play_audio, args=(argv[1],))
        thread1.start()

        thread2 = threading.Thread(target=play_video, args=(
            cap, width, height, frame_duration))
        thread2.start()

    thread1.join()
    thread2.join()

    cap.release()


if __name__ == "__main__":
    main(sys.argv)
