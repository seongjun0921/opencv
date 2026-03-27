import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math
import random

# === [사용자 원본 로직 유지] ===
ANGLE_MIN_DEG = 0
ANGLE_MAX_DEG = 359
NUM_POINTS = 360
RANGE_MIN = 0.12 
RANGE_MAX = 3.5 

def make_the_wall(ranges, center_deg, width_deg):
    half_width = width_deg // 2
    for offset in range(-half_width, half_width + 1):
        idx = (center_deg + offset) % NUM_POINTS
        ranges[idx] = 0.4

def generate_single_scan(pattern_name):
    # create_empty_scan의 로직을 포함
    ranges = [float(RANGE_MAX) for _ in range(NUM_POINTS)]
    if pattern_name == "front_wall and right_wall":
        make_the_wall(ranges, center_deg=0, width_deg=40)
        make_the_wall(ranges, center_deg=90, width_deg=30)
    elif pattern_name == "front_wall and left_wall":
        make_the_wall(ranges, center_deg=0, width_deg=40)
        make_the_wall(ranges, center_deg=270, width_deg=30)
    elif pattern_name == "right_all and left_wall":
        make_the_wall(ranges, center_deg=90, width_deg=30)
        make_the_wall(ranges, center_deg=270, width_deg=30)
    return ranges
# ============================

class LidarMockNode(Node):
    def __init__(self):
        super().__init__('lidar_mock_node')
        # /scan 토픽으로 메시지 발행 설정
        self.publisher_ = self.create_publisher(LaserScan, 'scan', 10)
        # 2.0초 주기로 타이머 설정
        self.timer = self.create_timer(2.0, self.timer_callback)
        self.patterns = ["front_wall and right_wall", "front_wall and left_wall", "right_wall and left_wall"]
        self.get_logger().info("Lidar Mock Node has started (2s interval)")

    def timer_callback(self):
        scan_msg = LaserScan()
        
        # ROS 2 필수 헤더 정보
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = 'laser_frame'
        
        # 기존 설정값들 대입 (라디안 변환 포함)
        scan_msg.angle_min = math.radians(ANGLE_MIN_DEG)
        scan_msg.angle_max = math.radians(ANGLE_MAX_DEG)
        scan_msg.angle_increment = math.radians(1.0)
        scan_msg.range_min = RANGE_MIN
        scan_msg.range_max = RANGE_MAX

        # 원본 함수 호출하여 거리 데이터 생성
        chosen_pattern = random.choice(self.patterns)
        scan_msg.ranges = generate_single_scan(chosen_pattern)
        scan_msg.intensities = [100.0] * NUM_POINTS

        # 토픽 발행
        self.publisher_.publish(scan_msg)
        self.get_logger().info(f'Published Scan Pattern: {chosen_pattern}')

def main(args=None):
    rclpy.init(args=args)
    node = LidarMockNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()