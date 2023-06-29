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
    """A class representing a video stream track for a bouncing ball animation.
    
    This class extends the `VideoStreamTrack` class and implements the animation logic
    for a bouncing ball. The animation is performed on a screen defined by the dimensions
    provided.
    
    Attributes:
        coords (Queue): A queue to store the coordinates of the ball during animation.
        counter (int): A counter variable.
        ball_pos_x (int): The x-coordinate of the ball's position.
        ball_pos_y (int): The y-coordinate of the ball's position.
        velocity_x (int): The velocity of the ball along the x-axis.
        velocity_y (int): The velocity of the ball along the y-axis.
        screen_width (int): The width of the animation screen.
        screen_height (int): The height of the animation screen.
    """
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
        """Receive a video frame with the bouncing ball animation.
        
        This method calculates the next position of the ball based on its velocity and
        updates the ball's position accordingly. It checks for collisions with the screen
        boundaries and changes the velocity accordingly. It then generates an image with
        the updated ball position and returns it as a video frame.
        
        Returns:
            VideoFrame: The video frame containing the bouncing ball animation.
        """
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
    """Log a message for a channel.
    
    This function logs a message with the provided channel's label, the current time `t`,
    and the given message.
    
    Args:
        channel: The channel object.
        t: The current time.
        message: The message to log.
    """
    print("channel(%s) %s %s" % (channel.label, t, message))

def channel_send(channel, message):
    """Send a message through a channel.
    
    This function sends a message through the provided channel and logs the sent message.
    
    Args:
        channel: The channel object.
        message: The message to send.
    """
    channel_log(channel, ">", message)
    channel.send(message)

async def run(pc, signaling):
    """Run the bouncing ball animation and handle signaling.
    
    This function runs the bouncing ball animation by creating a `BouncingBallVideoStreamTrack`
    object and adding it as a track to the provided `pc` (peer connection) object. It also
    handles the signaling process by connecting to the signaling server, creating and sending
    local descriptions, receiving remote descriptions, adding ICE candidates, and responding
    to BYE signals.
    
    Args:
        pc: The peer connection object.
        signaling: The signaling object for communication.
    """
    await signaling.connect()
    bouncingBallTrack = BouncingBallVideoStreamTrack()

    channel = pc.createDataChannel("chat")
    @channel.on("open")
    def on_open():
        """Handle an open channel event.
    
        This function is called when the data channel is opened and performs the action of
        sending a "ping" message through the channel.
        """
        print("ping")
        channel_send(channel, "ping")

    @channel.on("message")
    def on_message(message):
        """Handle a received message on the channel.
    
        This function is called when a message is received on the data channel. It extracts
        the coordinates from the received message, retrieves the actual coordinates from the
        `bouncingBallTrack` object, and logs the received coordinates and the error between
        the received and actual coordinates.
        
        Args:
            message: The received message containing the coordinates.
        """
        x, y = message.split(",")
        X, Y = int(x), int(y)
        print(X,Y)
        actualX, actualY = bouncingBallTrack.coords.get()
        print(actualX, actualY)
        print(f"Received coordinates: ({X},{Y})")
        print(f"Error: ({abs(X - actualX)}, {abs(Y - actualY)})")


    def add_tracks():
        """Add tracks to the peer connection.
    
        This function adds the bouncing ball track to the peer connection object `pc`.
        """
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
    signaling = TcpSocketSignaling('0.0.0.0', 1234)

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