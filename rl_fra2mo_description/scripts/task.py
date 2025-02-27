#! /usr/bin/env python3
from geometry_msgs.msg import PoseStamped, Twist, TransformStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster
from visualization_msgs.msg import Marker
import rclpy
import time
from tf_transformations import quaternion_from_euler, euler_from_quaternion
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

def create_pose(x, y, z=0.0, yaw=0.0):
    """Crea un PoseStamped per una posizione specifica."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = z
    # Orientamento in quaternioni (usando solo yaw)
    q = quaternion_from_euler(0.0, 0.0, yaw)
    pose.pose.orientation.x = q[0]
    pose.pose.orientation.y = q[1]
    pose.pose.orientation.z = q[2]
    pose.pose.orientation.w = q[3]
    return pose


class TaskNode(Node):
    def __init__(self):
        super().__init__('task_node')

        # Broadcaster TF Statico
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)

        # Publisher per il comando di velocità
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscriber per rilevare il marker
        self.marker_pose = None
        self.marker_orientation = None
        self.create_subscription(Marker, '/aruco_detect/marker', self.marker_callback, 10)

    def marker_callback(self, msg):
        """Callback per il rilevamento del marker."""
        self.marker_pose = msg.pose.position  # Salva la posizione del marker
        self.marker_orientation = msg.pose.orientation  # Salva l'orientamento del marker


    def stop_robot(self):
        """Invia un comando di stop al robot."""
        twist = Twist()
        self.cmd_vel_publisher.publish(twist)
        self.get_logger().info("Robot stopped.")

def main():
    rclpy.init()

    # Inizializza il nodo ROS2
    node = TaskNode()

    # Inizializza il navigatore
    navigator = BasicNavigator()

    # Waypoints specifici
    initial_pose = create_pose(0.0, 0.0)  # Posizione iniziale
    obstacle_9_pose = create_pose(4.4, -1.8, yaw=-1.0)  # Vicino all'ostacolo 9
    intermediate_pose = create_pose(2.5, -0.4)  # Punto intermedio

    # Activate Nav2
    navigator.waitUntilNav2Active()

    # Step 1: Vai alla posizione iniziale
    print("Going to initial position...")
    navigator.goToPose(initial_pose)
    while not navigator.isTaskComplete():
        pass
    if navigator.getResult() != TaskResult.SUCCEEDED:
        print("Failed to reach initial position!")
        exit(1)

    # Step 2: Vai in prossimità dell'ostacolo 9
    print("Moving to obstacle 9...")
    navigator.goToPose(obstacle_9_pose)
    while not navigator.isTaskComplete():
        pass
    if navigator.getResult() != TaskResult.SUCCEEDED:
        print("Failed to reach obstacle 9!")
        exit(1)

    # Pausa di 5 secondi
    #print("Pausing for 5 seconds...")
    #time.sleep(5)

    # Step 3: Torna alla posizione iniziale tramite punto intermedio
    navigator.goToPose(intermediate_pose)
    while not navigator.isTaskComplete():
        pass
    if navigator.getResult() != TaskResult.SUCCEEDED:
        print("Failed to reach intermediate point!")
        exit(1)

    print("Returning to initial position...")
    navigator.goToPose(initial_pose)
    while not navigator.isTaskComplete():
        pass
    if navigator.getResult() == TaskResult.SUCCEEDED:
        print("Task completed successfully!")

        # Ferma il movimento del robot
        node.stop_robot()
    else:
        print("Failed to return to initial position!")

    # Mantenere il nodo attivo
    print("Node will remain active. Press Ctrl+C to exit.")
    rclpy.spin(node)  # Mantiene il nodo attivo

if __name__ == '__main__':
    main()

