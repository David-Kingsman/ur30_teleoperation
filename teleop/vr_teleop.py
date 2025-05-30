import socket
import numpy as np

from UR30_RTDE.rtde.rtde import RTDE
from teleop.gripper_request import GripperRequest
from teleop.vr_tracker import VRTracker


def main():
    # Create a TCP socket to listen to Unity
    unity_ip = "127.0.0.1"
    port = 5555

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((unity_ip, port))
    print("Connected to Unity server")

    # Initialize the teleoperation class
    rtde = RTDE("192.168.1.102")
    # Initialize the gripper class
    gripper = GripperRequest("130.215.216.42")
    # Teleop control
    teleop = VRTracker(
        rtde,
        gripper,
        rate=0.01,  # Control rate in seconds
        smooth_step=0.05,  # Smoothing step size, smaller is smoother
        pos_mapping=(0.5, 0.5, 0.5),  # x, y, z mapping scaling
    )

    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8").strip()
            if not data:
                break
            # Split the data by newline
            data = data.split('\n')
            if not data or not data[0]:
                continue

            # Parse data: x, y, z, qx, qy, qz, qw, button1, button2
            # Use the latest one
            data = data[0].split(',')
            # partial data, reject
            if len(data) < 9:
                continue

            values = list(map(float, data))
            position = values[:3]
            rotation = values[3:7]
            button1 = bool(values[7])
            button2 = bool(values[8])

            # Toggle pause/resume with button1
            if button1:
                if teleop.paused:
                    print("Resuming teleoperation...")
                    teleop.resume(position + rotation)
                else:
                    print("Pausing teleoperation...")
                    teleop.pause()

            # Trigger the gripper with button2
            if button2:
                if teleop.gripper_open:
                    print("Closing gripper!")
                else:
                    print("Opening gripper!")
                teleop.trigger_gripper()

            # Track
            teleop.track(position + rotation)

    except KeyboardInterrupt:
        print("Closing connection...")
    finally:
        rtde.stop_script()
        client_socket.close()

if __name__ == "__main__":
    main()
