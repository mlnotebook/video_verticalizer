""" Creates a vertical line for each frame of a video file. Concatenates
them into a piece of artwork.

Script written by R.Robinson (https://github.com/mlnotebook/video_verticalizer) 07/2020
"""

import cv2
import os
import numpy as np
from tqdm import tqdm
from imutils.video import FPS
from PIL import Image
import configparser


def upscale(image, width, height):
    """Increases the size of an image using nearest-neighbour interpolation.

    Preserves the lines in the final ouput image rather than using linear interp.

    Args:
        image (numpy.ndarray): the image to be resized. 3 channel RGB.
        width (int): the final image width.
        height (int): the final image height.
    Returns:
        upscaled_image (numpy.ndarray): the rescaled image [width, height, channels]
    """
    upscaled_image = cv2.resize(image, (width, height), interpolation=0)
    return upscaled_image


def check_input_files(config, video_root):
    """Checks if video files exist at the given filepaths.

    Args:
        config (dict): the config dictionary read by configparser.
        video_root (str): the path to the directory containing the video files.
    Raises:
        Exception if file not found.
    """
    movie_dict = config.sections()[1:]  # Removes the 'CONFIG' section.
    for this_movie in movie_dict:
        filepath = os.path.join(video_root, config[this_movie]['filename'])
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File does not exist at {filepath}")


def main(config):
    """Video verticalizer main script."""
    movie_dict = config.sections()[1:]  # Removes the 'CONFIG' section.
    try:
        for movie in movie_dict:
            movie_filename = str(config[movie]['filename'])
            start_time = float(config[movie]['start_time'])
            end_time = float(config[movie]['end_time'])
            video_file = os.path.join(video_root, movie_filename)

            output_dir = output_root + f'_{crop_ratio}'
            os.makedirs(output_dir, exist_ok=True)
            save_filename = f"{os.path.basename(video_file).split('.')[0]}_{crop_ratio}{output_format}"
            save_name = os.path.join(output_dir, save_filename)

            if os.path.exists(save_name):
                continue

            cap = cv2.VideoCapture(video_file)
            fps = FPS().start()

            frames_per_second = int(cap.get(cv2.CAP_PROP_FPS))
            total_number_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if end_time == -1:
                end_time = total_number_of_frames / frames_per_second

            start_time_ms = start_time * 1000
            end_time_ms = end_time * 1000
            movie_time = end_time_ms - start_time_ms
            duration = movie_time / 1000

            start_frame = int((start_time_ms / 1000) * frames_per_second)
            number_of_frames = int((movie_time / 1000) * frames_per_second)
            frame_skip = int(np.ceil(number_of_frames / canvas_shape[1]))
            frames_to_take = int(number_of_frames // frame_skip)

            canvas = np.ones([canvas_shape[0], 1, 3]).astype(np.uint8)
            line_width = 1
            new_line = np.ones([canvas_shape[0], line_width, 3]).astype(np.uint8)

            print(f'movie: {movie}')
            print(f'vid_length: {duration}')
            print(f'frames_per_second: {frames_per_second}')
            print(f'num_frames: {number_of_frames}')
            print(f'frames_to_take: {frames_to_take}')
            print(f'frame_skip: {frame_skip}')
            print(f'output_shape: [{canvas.shape[0]}, {frames_to_take}, {canvas.shape[2]}]')

            force_quit = False
            for frame_idx in tqdm(range(start_frame, number_of_frames, frame_skip), desc='Frames'):
                if cap.get(cv2.CAP_PROP_POS_MSEC) >= end_time_ms:
                    # END OF MOVIE REACHED
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                grabbed, frame = cap.read()

                if not grabbed:
                    # COULD NOT GET NEXT FRAME (END OF FILE)
                    break

                if frame is not None:
                    h, w, c = frame.shape
                    frame = frame[h // 2 - H_CROP_SIZE:h // 2 + H_CROP_SIZE, w // 2 - W_CROP_SIZE:w // 2 + W_CROP_SIZE]
                    average_color = np.mean(frame, (0, 1)).astype(np.uint8)
                    this_line = np.array(new_line * average_color).astype(np.uint8)
                    canvas = np.hstack([canvas, this_line])

                    if show_progress:
                        cv2.imshow('frame', canvas)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        force_quit = True
                        break

                fps.update()

            if not force_quit:
                RGBimage = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
                UpscaleRGBimage = upscale(RGBimage, final_width, final_height)
                PILimage = Image.fromarray(UpscaleRGBimage)
                print(f'Output: {save_name}\n')
                PILimage.save(save_name)

    except KeyboardInterrupt:
        print('Stopped by user')


if __name__ == "__main__":
    # READ THE CONFIG FILE
    config = configparser.ConfigParser()
    config.read('./config.cfg')

    # SET CONFIG VARIABLES
    canvas_shape = [int(config['CONFIG']['canvas_height']), int(config['CONFIG']['canvas_width']), 3]
    crop_ratio = float(config['CONFIG']['crop_ratio'])
    video_root = str(config['CONFIG']['video_root'])
    final_width = int(config['CONFIG']['final_width'])
    final_height = int(config['CONFIG']['final_height'])
    output_root = str(config['CONFIG']['output_root'])
    output_format = str(config['CONFIG']['output_format'])
    show_progress = bool(config['CONFIG']['show_progress'])

    H_CROP_SIZE = int(canvas_shape[0] * crop_ratio) // 2
    W_CROP_SIZE = int(canvas_shape[1] * crop_ratio) // 2

    # RUN  SCRIPT
    main(config)
