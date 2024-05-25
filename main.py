#!/usr/bin/env python3

import os
import sys
import cv2
import time
import threading

from numba import njit
from moviepy.editor import VideoFileClip

res = 80
density = " .,-~:;=!*#$@"

THRESHOLD = 0.005
TIME_DUMP_FILE = "time_dump.tmp"


def print_loading_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration  - Required  : current iteration (Int)
        total      - Required  : total iterations (Int)
        prefix     - Optional  : prefix string (Str)
        suffix     - Optional  : suffix string (Str)
        decimals   - Optional  : positive number of decimals in percent complete (Int)
        length     - Optional  : character length of bar (Int)
        fill       - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    time_elapsed = time.time() - start_time
    time_per_iteration = time_elapsed / (iteration + 1)
    time_remaining = time_per_iteration * (total - iteration - 1)
    eta = time.strftime("%H:%M:%S", time.gmtime(time_remaining))
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix} ETA: {eta}')
    sys.stdout.flush()
    if iteration == total:
        print()


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
    global start_time
    start_time = time.time()

    cache = []
    no_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i in range(no_of_frames):
        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (width, height))
        grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        output = generate_frame(width, height, grayscale)
        cache.append("".join(output))
        print_loading_bar(i + 1, no_of_frames, prefix='Progress',
                          suffix='Complete', length=50)

    return cache


def play_cached_video(cache, frame_duration):
    thread = threading.Thread(target=play_audio, args=(sys.argv[1],))
    thread.start()

    for frame in cache:
        start_time = time.time()
        print("\033[H\033[J", end="")
        print(frame)
        elapsed_time = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed_time)
        time.sleep(sleep_time)

    thread.join()


def play_video(cap, width, height, frame_duration):
    thread = None

    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (width, height))
        grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        print("\033[H\033[J", end="")

        output = generate_frame(width, height, grayscale)

        if thread is None:
            thread = threading.Thread(target=play_audio, args=(sys.argv[1],))
            thread.start()

        print("".join(output))

        elapsed_time = time.time() - start_time
        sleep_time = max(0, frame_duration - elapsed_time)
        time.sleep(sleep_time)

    thread.join()


def get_elapsed_time(cap, width, height):
    file = open(TIME_DUMP_FILE, "w")

    start_time = time.time()
    _, frame = cap.read()

    resized = cv2.resize(frame, (width, height))
    grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    output = generate_frame(width, height, grayscale)
    file.write("".join(output))

    elapsed_time = time.time() - start_time

    file.close()

    return elapsed_time


def main():
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <video> [res]")
        exit(1)

    global res

    if len(sys.argv) == 3:
        res = int(sys.argv[2])

    cap = cv2.VideoCapture(sys.argv[1])

    if not cap.isOpened():
        print(f"Error: Cannot open video {sys.argv[1]}")
        exit(1)

    xh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    xw = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    width = res
    height = int(width / xw * xh / 2)

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps

    _ = get_elapsed_time(cap, width, height)  # warm up
    elapsed_time = get_elapsed_time(cap, width, height)

    try:
        os.remove(TIME_DUMP_FILE)
    except:
        print("Error: Cannot remove time dump file")

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if elapsed_time > frame_duration - THRESHOLD:
        cache = build_cache(cap, width, height)
        play_cached_video(cache, frame_duration)
    else:
        play_video(cap, width, height, frame_duration)

    print("\033[H\033[J", end="")

    cap.release()


if __name__ == "__main__":
    main()
