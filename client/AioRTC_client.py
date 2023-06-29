import argparse
import asyncio
import logging
import math

import cv2
import numpy
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from threading import Thread
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
from multiprocessing import Queue, Process, Value

class FlagVideoStreamTrack(VideoStreamTrack, Thread):
    def __init__(self, track):
        super().__init__()  # don't forget this!
        Thread.__init__(self)
        self.queue = Queue()
        self.track = track
        self.num_frame = 0
        print("track id: ", track.id)

    async def recv(self):
        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")
        self.num_frame +=1
        print(frame)
        cv2.imwrite("xyz"+str(self.num_frame)+".png",img)
        return frame
      
        



async def run(pc, player, recorder, signaling, role):
    # def add_tracks():
    #     if player and player.audio:
    #         pc.addTrack(player.audio)

    #     if player and player.video:
    #         pc.addTrack(player.video)
    #     else:
    #         pc.addTrack(FlagVideoStreamTrack(role))

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        # recorder.addTrack(track)
        pc.addTrack(FlagVideoStreamTrack(track))

    # connect signaling
    await signaling.connect()

    # if role == "offer":
    #     # send offer
    #     add_tracks()
    #     await pc.setLocalDescription(await pc.createOffer())
    #     await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            # await recorder.start()

            if obj.type == "offer":
                # send answer
                # add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
                print("XXX")
        elif isinstance(obj, RTCIceCandidate):
            print("YYY")
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        player = None

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
        print("RECORD TO ")
    else:
        recorder = MediaBlackhole()
        print("NOT RECORD TO ")

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                player=player,
                recorder=recorder,
                signaling=signaling,
                role=args.role,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
