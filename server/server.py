import argparse
import asyncio
import logging
import math

import cv2
import numpy as np
from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling, TcpSocketSignaling
from threading import Thread
from collections import deque
from multiprocessing import Queue, Process
class FlagVideoStreamTrack(VideoStreamTrack, Thread):
    def __init__(self, role):
        super().__init__()  # don't forget this!
        Thread.__init__(self)
        self.queue = Queue()
        self.start()
        self.role = role
        self.counter = 0

        self.ball_pos_x = 50
        self.ball_pos_y = 50
        self.velocity_x = 5
        self.velocity_y = 5

        # Set the dimensions of the screen
        self.screen_width = 640
        self.screen_height = 480

       
           

    async def recv(self):

        self.ball_pos_x += self.velocity_x
        self.ball_pos_y += self.velocity_y
        print(self.ball_pos_x, self.ball_pos_y)

            # Check for collision with the screen boundaries
        if self.ball_pos_x <= 0 or self.ball_pos_x >= self.screen_width:
            self.velocity_x *= -1
        if self.ball_pos_y <= 0 or self.ball_pos_y >= self.screen_height:
            self.velocity_y *= -1
        screen = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        # Clear the screen
        screen.fill(0)

            # Draw the ball on the screen
        cv2.circle(screen, (self.ball_pos_x, self.ball_pos_y), 10, (0, 0, 255), -1)
            # cv2.waitKey(1)
            # Display the frame
            # self.queue.put(screen)
        img = screen
        frame = VideoFrame.from_ndarray(img, format ="bgr24")
        # print(frame)
        pts, time_base = await self.next_timestamp()
        frame.pts = pts
        frame.time_base = time_base
        return frame


async def run_off_ans(pc, player, recorder, signaling, role):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
        else:
            pc.addTrack(FlagVideoStreamTrack(role))

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)

    # connect signaling
    await signaling.connect()
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    # parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = TcpSocketSignaling('localhost', 1234)
    role = "offer"
    pc = RTCPeerConnection()

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        player = None

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run_off_ans(
                pc=pc,
                player=player,
                recorder=recorder,
                signaling=signaling,
                role=role,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())