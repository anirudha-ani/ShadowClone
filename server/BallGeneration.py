import cv2
import numpy as np
import os


def hasDisplay():
    return os.environ.get('DISPLAY') is None

def isRunningInDocker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

# Set the dimensions of the frame
width = 640
height = 480

# Set the initial position and velocity of the ball
ball_pos = [50, 50]
velocity = [1, 1]

# Create a black canvas as the background
frame = np.zeros((height, width, 3), dtype=np.uint8)

# Create an OpenCV window
if not hasDisplay():
    cv2.namedWindow("Ball Bouncing", cv2.WINDOW_NORMAL)

while True:
    # Update the ball position
    ball_pos[0] += velocity[0]
    ball_pos[1] += velocity[1]

    # Check if the ball hits the walls
    if ball_pos[0] <= 0 or ball_pos[0] >= width:
        velocity[0] *= -1
    if ball_pos[1] <= 0 or ball_pos[1] >= height:
        velocity[1] *= -1

    # Draw the ball on the frame
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.circle(frame, tuple(ball_pos), 10, (255, 0, 255), -1)

    # Display the frame in the OpenCV window
    if not hasDisplay():
        cv2.imshow("Ball Bouncing", frame)
        print(ball_pos[0] , ball_pos[1])

        # Wait for a key press and check if 'q' is pressed to exit the loop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# Release the OpenCV window and cleanup
if not hasDisplay():
    cv2.destroyAllWindows()
