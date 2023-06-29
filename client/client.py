import argparse
import asyncio
import logging
import math

import cv2
import numpy as np
import os
from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaStreamTrack
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling, TcpSocketSignaling
from threading import Thread
from multiprocessing import Queue, Process, Value
import time

data_channel = None

class BouncingBallVideoStreamTrack(VideoStreamTrack):
    """A class representing a video stream track for a bouncing ball animation and object detection.
    
    This class extends the `VideoStreamTrack` class and implements the logic for receiving video frames,
    performing object detection on the frames, and sending the coordinates of the detected object through
    a data channel.
    
    Attributes:
        track: The underlying video stream track.
        queue (Queue): A queue to store the received video frames.
        num_frame (int): The number of received frames.
        x (Value): A shared variable to store the x-coordinate of the detected object.
        y (Value): A shared variable to store the y-coordinate of the detected object.
        pc: The RTCPeerConnection object.
        signaling: The signaling object for communication.
    """
    def __init__(self, track, pc, signaling):
        super().__init__()
        self.track = track
        print("track id: ", track.id)
        self.queue = Queue()
        self.num_frame=0

        self.x = Value('i', 0)
        self.y = Value('i', 0)
        self.pc = pc
        self.signaling = signaling


    async def send_coords(self,x,y):
        """Send the coordinates of the detected object through the data channel.
        
        This method sends the provided x and y coordinates as a string through the data channel.
        
        Args:
            x: The x-coordinate of the detected object.
            y: The y-coordinate of the detected object.
        """
        global data_channel
        data_channel.send(str(x)+","+str(y))
        await asyncio.sleep(1)
                
    async def recv(self):
        """Receive video frames, perform object detection, and send object coordinates.
        
        This method continuously receives video frames from the underlying track. It performs object
        detection on the received frames, retrieves the coordinates of the detected object, and sends
        the coordinates through a data channel. It runs as an infinite loop until interrupted.
        
        Returns:
            None
        """
        while True:
            frame = await self.track.recv()
            self.num_frame += 1
            img = frame.to_ndarray(format="bgr24")
            # comment out the next line to save received images
            # cv2.imwrite(str(self.num_frame)+".png",img)
            self.queue.put(img)
            time.sleep(1)
            p = Process(target=process_a, args=(self.queue, self.x, self.y))
            p.start()
            p.join()
            x, y = self.x.value, self.y.value
            asyncio.ensure_future(self.send_coords(x,y))
            p.close()

def process_a(queue, x, y):
    """Perform object detection on an image from the queue and retrieve object coordinates.
    
    This function receives an image from the provided queue, performs object detection on the image
    to find a specific color object (red), and calculates the centroid (x, y coordinates) of the
    largest detected contour. The calculated coordinates are stored in the shared variables `x` and `y`.
    
    Args:
        queue: The queue containing the images for object detection.
        x: The shared variable to store the x-coordinate of the detected object.
        y: The shared variable to store the y-coordinate of the detected object.
    """
    image = queue.get()
    hsv_frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for red color in HSV
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])

    # Create a mask for red pixels in the frame
    red_mask = cv2.inRange(hsv_frame, lower_red, upper_red)

    # Apply morphological operations to remove noise
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

    # Find contours in the mask
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate over the contours and find the centroid of the largest contour (ball)
    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        cx = int(M["m10"] / M["m00"])  # X coordinate of the centroid
        cy = int(M["m01"] / M["m00"])  # Y coordinate of the centroid
        
        x.value = cx
        y.value = cy
        print(x.value,y.value)
    else:
        x.value = 0
        y.value = 0
        print("No Ball On the screen")

def channel_log(channel, t, message):
    """Log a message for a data channel.
    
    This function logs a message with the provided data channel's label, the current time `t`,
    and the given message.
    
    Args:
        channel: The data channel object.
        t: The current time.
        message: The message to log.
    """
    print("channel(%s) %s %s" % (channel.label, t, message))


def channel_send(channel, message):
    """Send a message through a data channel and log the sent message.
    
    This function sends a message through the provided data channel and logs the sent message.
    
    Args:
        channel: The data channel object.
        message: The message to send.
    """
    channel_log(channel, ">", message)
    channel.send(message)
    
async def run_off_ans(pc, recorder, signaling):
    """Run the object detection and video streaming application and handle signaling.
    
    This function establishes the connection with the signaling server, sets up event handlers
    for the data channel and incoming tracks, and runs the object detection and video streaming loop.
    It continuously listens for signaling messages, sets the remote description, and sends the local
    description based on the received offer. It also handles ICE candidates and terminates the loop
    when receiving the BYE signal.
    
    Args:
        pc: The RTCPeerConnection object.
        recorder: The media recorder object to write received media to a file.
        signaling: The signaling object for communication.
    """
    await signaling.connect()

    @pc.on("datachannel")
    def on_datachannel(channel):
        global data_channel
        channel_log(channel, "-", "created by remote party")
        data_channel = channel
        @channel.on("message")
        def on_message(message):
            if message == "ping":
                print("Channel is ready to send messages")

    @pc.on("track")
    async def on_track(track):
        global data_channel
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)
        print(data_channel)
        bbTrack = BouncingBallVideoStreamTrack(track, pc, signaling)
        # pc.addTrack(bbTrack)
        await bbTrack.recv()

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    serverIP = os.environ.get('SERVERIP')
    if serverIP == None:
        serverIP = '0.0.0.0'
    signaling = TcpSocketSignaling(serverIP, 1234)
    pc = RTCPeerConnection()

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
                recorder=recorder,
                signaling=signaling
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
