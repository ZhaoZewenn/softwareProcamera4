#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四摄像头标定工具（网络流版）
为每个摄像头标定魔方角点，生成 points_streams.json
"""
import cv2
import json
import os
import numpy as np

# 摄像头流地址（根据您的实际IP和端口修改）
CAM_STREAMS = {
    'top': "http://192.168.0.250:8001/stream",
    'bottom': "http://192.168.0.250:8002/stream",
    'left': "http://192.168.0.250:8003/stream",
    'right': "http://192.168.0.250:8004/stream"
}

POINTS_CONFIG_FILE = "points_streams.json"
POINTS_COUNT = {'top': 6, 'bottom': 6, 'left': 4, 'right': 4}
RADIUS = 8

class DraggablePoints:
    def __init__(self, width, height, point_count):
        self.width = width
        self.height = height
        self.point_count = point_count
        self.points = []
        self.dragging_index = -1
        self._init_default_points()

    def _init_default_points(self):
        if self.point_count == 6:
            for row in range(2):
                for col in range(3):
                    x = int((col + 0.5) * self.width / 3)
                    y = int((row + 0.5) * self.height / 2)
                    self.points.append([x, y])
        else:
            margin = 50
            self.points = [
                [margin, margin],
                [self.width - margin, margin],
                [margin, self.height - margin],
                [self.width - margin, self.height - margin]
            ]

    def draw(self, img):
        # 绘制四边形边框
        if self.point_count == 6:
            # 面1：0-3-4-1
            pts1 = [self.points[i] for i in [0, 3, 4, 1]]
            for i in range(4):
                cv2.line(img, pts1[i], pts1[(i+1)%4], (0, 255, 0), 2)
            # 面2：1-4-5-2
            pts2 = [self.points[i] for i in [1, 4, 5, 2]]
            for i in range(4):
                cv2.line(img, pts2[i], pts2[(i+1)%4], (0, 255, 0), 2)
        else:
            # 4点：顺序 0-1-3-2 （即 1→2→4→3）
            pts = [self.points[0], self.points[1], self.points[3], self.points[2]]
            for i in range(4):
                cv2.line(img, pts[i], pts[(i+1)%4], (0, 255, 0), 2)

        # 绘制圆点
        for i, (x, y) in enumerate(self.points):
            color = (0, 0, 255) if i == self.dragging_index else (255, 0, 0)
            cv2.circle(img, (x, y), RADIUS, color, -1)
            cv2.putText(img, str(i+1), (x-5, y+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def handle_mouse(self, event, x, y):
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, (px, py) in enumerate(self.points):
                if (x - px) ** 2 + (y - py) ** 2 <= RADIUS ** 2:
                    self.dragging_index = i
                    return True
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging_index >= 0:
            self.points[self.dragging_index] = [x, y]
            return True
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_index = -1
            return True
        return False

def main():
    saved = {}
    if os.path.exists(POINTS_CONFIG_FILE):
        with open(POINTS_CONFIG_FILE, 'r') as f:
            saved = json.load(f)
        print(f"已加载 {len(saved)} 个摄像头的标定点")

    for name, url in CAM_STREAMS.items():
        count = POINTS_COUNT[name]
        print(f"\n正在标定 {name.upper()} 摄像头...")
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            print(f"❌ {name} 连接失败，请检查网络和地址")
            continue
        ret, frame = cap.read()
        if not ret:
            print(f"❌ {name} 无法获取画面")
            cap.release()
            continue
        h, w = frame.shape[:2]
        draggable = DraggablePoints(w, h, count)

        if name in saved and len(saved[name]) == count:
            draggable.points = saved[name]
            print(f"✅ 加载已有标定点")
        else:
            print(f"请拖动圆圈使其对准魔方的角点")
            print(f"   (6点: 两个面共6点; 4点: 一个面4点)")

        win = f"标定 {name.upper()}"
        cv2.namedWindow(win)
        cv2.setMouseCallback(win, lambda e, x, y, f, p: draggable.handle_mouse(e, x, y))

        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            display = frame.copy()
            draggable.draw(display)
            cv2.putText(display, f"Calibrate {name} - drag circles, press 's' to save, 'q' to skip",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.imshow(win, display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                saved[name] = draggable.points
                with open(POINTS_CONFIG_FILE, 'w') as f:
                    json.dump(saved, f, indent=2)
                print(f"✅ 已保存 {name} 标定点")
                break
            elif key == ord('q'):
                print(f"⏭ 跳过 {name}")
                break

        cap.release()
        cv2.destroyWindow(win)

    print(f"\n标定完成！结果保存在 {POINTS_CONFIG_FILE}")
    with open(POINTS_CONFIG_FILE, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()