# USAGE
# python motion_detector.py
# python motion_detector.py --video videos/example_01.mp4

import datetime
import time

import argparse
import cv2
import imutils
import logging
# import the necessary packages
from imutils.video import VideoStream
from io import BytesIO

from command import Command
from discord import Discord
from embedbuilder import EmbedBuilder

total_count = 0
command = Command()
discord = Discord()


def send_message(frame):
    global total_count
    total_count += 1
    print("Triggered %i times\n", total_count)

    global discord
    builder = EmbedBuilder()
    builder.set_image(("maybecat.png", frame))
    builder.set_title("Iz this Kat?")
    builder.set_description("use /tableflip to shoo away")
    embeds = builder.get_embeds()
    discord.send(embeds=embeds)


def main(args):
    discord.configure_discord(bot_token=args.get("bot_token", None),
                              channel_id=args.get("channel_id", None),
                              command=command,
                              logger=logging,
                              allowed_users=None)

    # if the video argument is None, then we are reading from webcam
    if args.get("video", None) is None:
        vs = VideoStream(src=0).start()
        time.sleep(2.0)

    # otherwise, we are reading from a video file
    else:
        vs = cv2.VideoCapture(args["video"])

    # initialize the first frame in the video stream
    first_frame = None

    # loop over the frames of the video
    while True:
        # grab the current frame and initialize the occupied/unoccupied
        # text
        frame = vs.read()
        frame = frame if args.get("video", None) is None else frame[1]
        text = "Unoccupied"

        # if the frame could not be grabbed, then we have reached the end
        # of the video
        if frame is None:
            break

        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the first frame is None, initialize it
        if first_frame is None:
            first_frame = gray
            continue

        # compute the absolute difference between the current frame and
        # first frame
        frame_delta = cv2.absdiff(first_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < args["min_area"]:
                continue

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Occupied"

        # draw the text and timestamp on the frame
        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # show the frame and record if the user presses a key
        cv2.imshow("Security Feed", frame)
        if text == "Occupied":
            bytes = cv2.imencode(".png", frame)[1].tostring()

            send_message(BytesIO(bytes))
            # Sleep for 10 seconds, to avoid spamming messages
            time.sleep(10)

        # cv2.imshow("Thresh", thresh)
        # cv2.imshow("Frame Delta", frame_delta)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key is pressed, break from the lop
        if key == ord("q"):
            break

        # Update keyframe
        first_frame = gray

        # Sleep 1 seconds
        time.sleep(1)

    # cleanup the camera and close any open windows
    vs.stop() if args.get("video", None) is None else vs.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", help="path to the video file")
    ap.add_argument("-a", "--min-area", type=int, default=1500, help="minimum area size")
    ap.add_argument("-b", "--bot-token", type=str, help="the bot token for discord")
    ap.add_argument("-c", "--channel-id", type=str, help="the channel to post to, and listen on")
    main(vars(ap.parse_args()))
