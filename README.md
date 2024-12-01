I have created a dirt detection system using OpenCV and Flask to identify stains in a video feed. The system uses a camera to capture the video feed and then processes it to detect dirt or stains. The detection results are then logged to a Firebase database and a local text file.

The system uses a HSV color range to define the color of the dirt or stain, and then uses contour detection to identify the area of the dirt or stain. The system also uses thresholds to filter out false positives and ensure that only actual dirt or stains are detected.

The system can be accessed through a web interface, where users can view the video feed and see the detection results in real-time. The system also provides a feature to download the detection logs as a text file.

I hope this system can be useful in detecting dirt or stains in various applications, such as cleaning robots or quality control systems.
