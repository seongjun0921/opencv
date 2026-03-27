import json
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pymysql
import roslibpy

# 데이터베이스 연결 정보 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '0000',
    'database': 'robot_db'
}

# ROS 브릿지 클라이언트 및 Topic 설정
client = roslibpy.Ros(host='localhost', port=9090)
velocity_pub = roslibpy.Topic(client, '/turtle1/cmd_vel', 'geometry_msgs/Twist')
listener = roslibpy.Topic(client, '/scan', 'sensor_msgs/LaserScan')


def save_to_mysql(ranges_list, action_name):
    """Lidar 스캔 데이터와 결정된 주행 액션을 MySQL DB에 저장합니다."""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        sql = "INSERT INTO lidardata (ranges, `when`, action) VALUES (%s, %s, %s)"
        val = (json.dumps(ranges_list), datetime.now(), action_name)

        cursor.execute(sql, val)
        conn.commit()

    except Exception as e:
        print(f"[Error] Failed to save to database: {e}")
    finally:
        cursor.close()
        conn.close()


def get_parsed_robot_data():
    """DB에 저장된 Lidar 데이터를 AI 학습용 Pandas 데이터프레임(361열)으로 파싱하여 반환합니다."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = "SELECT ranges, action FROM lidardata"
        df_raw = pd.read_sql(query, conn)
        conn.close()

        print(f"[Info] Successfully loaded {len(df_raw)} records from DB.")

        parsed_list = []
        for _, row in df_raw.iterrows():
            # JSON 문자열을 리스트로 변환 후 마지막 열에 action 라벨 추가
            lidar_list = json.loads(row['ranges'])
            lidar_list.append(row['action'])
            parsed_list.append(lidar_list)

        # 360개의 각도 컬럼(deg_0 ~ deg_359)과 1개의 액션 컬럼 생성
        column_names = [f"deg_{i}" for i in range(360)] + ["action"]
        df_final = pd.DataFrame(parsed_list, columns=column_names)

        return df_final

    except Exception as e:
        print(f"[Error] Failed to parse data: {e}")
        return None


def decide_motion(message):
    """Lidar 센서 값을 바탕으로 주행 방향을 결정하고, 로봇 제어 및 DB 저장을 수행합니다."""
    ranges_list = message.get('ranges', [])
    if len(ranges_list) < 360:
        return

    ranges = np.array(ranges_list)

    # 전방, 좌측, 우측 구역의 거리 평균 계산
    front = np.r_[ranges[350:360], ranges[0:10]]
    left = ranges[80:100]
    right = ranges[260:280]

    front_dist = np.mean(front)
    left_dist = np.mean(left)
    right_dist = np.mean(right)

    safe_dist = 0.5
    linear_v, angular_z = 0.0, 0.0

    # 장애물 회피 판단 로직
    if front_dist < safe_dist and right_dist < safe_dist:
        action = "turn_left"
        angular_z = 1.6
    elif front_dist < safe_dist and left_dist < safe_dist:
        action = "turn_right"
        angular_z = -1.6
    else:
        action = "go_forward"
        linear_v = 3.0

    print(f"Front Distance: {front_dist:.2f}m -> Action: {action}")

    # 거북이 주행 명령 Publish
    msg = roslibpy.Message({
        'linear': {'x': float(linear_v), 'y': 0.0, 'z': 0.0},
        'angular': {'x': 0.0, 'y': 0.0, 'z': float(angular_z)}
    })
    velocity_pub.publish(msg)

    # 현재 상태 DB 기록
    save_to_mysql(ranges_list, action)


def main():
    # 1. 시작 전 기존 저장 데이터 파싱 테스트
    df = get_parsed_robot_data()
    if df is not None:
        print("\n[Info] Data Parsing Test Completed (Top 5 rows):")
        print(df.head())
        print(f"[Info] Final Data Shape: {df.shape}\n")

    # 2. ROS 통신 및 자율주행 루프 시작
    client.run()
    if client.is_connected:
        print("[Info] ROS Bridge Connected - Starting Autonomous Driving...")
        listener.subscribe(decide_motion)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Info] Terminating Autonomous Driving.")
            client.terminate()


if __name__ == '__main__':
    main()