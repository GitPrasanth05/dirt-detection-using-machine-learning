import cv2
import numpy as np
import os
from flask import Flask, render_template, Response, request, send_from_directory
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta


cred = credentials.Certificate("C:\\firebase dirt\\automatic-dirt-detection-firebase-adminsdk-f90eo-ec020060e5.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://automatic-dirt-detection-default-rtdb.firebaseio.com/'
})

output_dir = "errorpic"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(0)

lower = np.array([0, 0, 168])
upper = np.array([172, 111, 255])
threshold_value = 1300
background_threshold = 20000


log_file_path = "firebase_logs.txt"

last_log_time = datetime.min

app = Flask(__name__)

def get_next_filename(directory):
    existing_files = sorted(os.listdir(directory))
    if not existing_files:
        return "1.jpg"
    last_file = existing_files[-1]
    last_number = int(last_file.split('.')[0])
    next_number = last_number + 1
    return f"{next_number}.jpg"

def log_to_firebase(message, contour_area=None):
    global last_log_time

    current_time = datetime.now()
    if current_time - last_log_time < timedelta(seconds=3):
        return

    last_log_time = current_time
    time_str = current_time.strftime("%H:%M:%S")
    log_entry = {
        'time': time_str,
        'message': message
    }
    if contour_area is not None:
        log_entry['contour_area'] = contour_area
    ref = db.reference('logs')
    ref.push(log_entry)
    
    
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{log_entry['time']} - {log_entry['message']}\n")

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_processed_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        x1, y1, w1, h1 = int(frame.shape[1] * 0.3), int(frame.shape[0] * 0.3), int(frame.shape[1] * 0.4), int(frame.shape[0] * 0.4)
        roi = frame[y1:y1 + h1, x1:x1 + w1]

        hsv_image = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, lower, upper)

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        significant_contours = [contour for contour in contours if threshold_value < cv2.contourArea(contour) < background_threshold]

        if significant_contours:
            for contour in significant_contours:
                contour[:, 0, 0] += x1
                contour[:, 0, 1] += y1
                cv2.drawContours(frame, [contour], -1, (255, 0, 0), 2)
            cv2.putText(frame, "DIRT FOUND", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            filename = get_next_filename(output_dir)
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, frame)

            contour_areas = [cv2.contourArea(contour) for contour in significant_contours]
            for area in contour_areas:
                log_to_firebase("Dirt found", contour_area=area)
        else:
            cv2.putText(frame, "DIRT NOT FOUND", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            log_to_firebase("Dirt not found")

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_original')
def video_feed_original():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_processed')
def video_feed_processed():
    return Response(generate_processed_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end_program', methods=['POST'])
def end_program():
    global cap
    cap.release()
    cv2.destroyAllWindows()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return "Program terminated", 200


@app.route('/download_report')
def download_report():
    try:
        logs_directory = os.path.abspath("C:\\firebase check")
        
        logs_file_path = os.path.join(logs_directory, "firebase_logs.txt")
        
        with open(logs_file_path, "r") as file:
            logs_content = file.read()
        
        return logs_content
    except Exception as e:
        return str(e)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
