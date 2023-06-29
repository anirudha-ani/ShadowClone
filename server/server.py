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

class BouncingBallVideoStreamTrack(VideoStreamTrack, Thread):
    def __init__(self):
        super().__init__()  # don't forget this!
        Thread.__init__(self)
        self.coords = Queue()
        self.start()
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
        # print(self.ball_pos_x, self.ball_pos_y)

        # Check for collision with the screen boundaries
        if self.ball_pos_x <= 0 or self.ball_pos_x >= self.screen_width:
            self.velocity_x *= -1
        if self.ball_pos_y <= 0 or self.ball_pos_y >= self.screen_height:
            self.velocity_y *= -1
        img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        # Clear the screen
        img.fill(0)

        # Draw the ball on the screen
        cv2.circle(img, (self.ball_pos_x, self.ball_pos_y), 10, (0, 0, 255), -1)
        
        # add the ball cooridnate in a queue
        self.coords.put((self.ball_pos_x,self.ball_pos_y))
        
        frame = VideoFrame.from_ndarray(img, format ="bgr24")
        pts, time_base = await self.next_timestamp()
        frame.pts = pts
        frame.time_base = time_base

        return frame

def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))

def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)

async def run(pc, signaling):
    await signaling.connect()
    bouncingBallTrack = BouncingBallVideoStreamTrack()

    channel = pc.createDataChannel("chat")
    @channel.on("open")
    def on_open():
        print("ping")
        channel_send(channel, "ping")

    @channel.on("message")
    def on_message(message):
        x, y = message.split(",")
        X, Y = int(x), int(y)
        print(X,Y)
        actualX, actualY = bouncingBallTrack.coords.get()
        print(actualX, actualY)
        print(f"Received coordinates: ({X},{Y})")
        print(f"Error: ({abs(X - actualX)}, {abs(Y - actualY)})")


    def add_tracks():
        pc.addTrack(bouncingBallTrack)

    @pc.on("track")
    def on_track(track):
        pass

    # connect signaling
    
    add_tracks()
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

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
   
    parser.add_argument("--verbose", "-v", action="count")
    
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = TcpSocketSignaling('localhost', 1234)

    pc = RTCPeerConnection()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())