import sqlite3
import os
from keras.preprocessing import image
from keras import backend as K
from mrcnn.config import Config
from mrcnn.model import MaskRCNN
import numpy as np
import cv2

import tensorflow as tf

physical_devices = tf.compat.v1.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

class CarConfig(Config):
    NAME = "car"
    NUM_CLASSES = 1 + 80  # Background + car
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    DETECTION_MIN_CONFIDENCE = 0.6

class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck']

def get_car_boxes(boxes, class_ids):
    car_boxes = []
    truck_boxes = []
    motorcycle_boxes = []

    for i, class_id in enumerate(class_ids):
        if class_id == 3:  # Car
            car_boxes.append(boxes[i])
        elif class_id == 8:  # Truck
            truck_boxes.append(boxes[i])
        elif class_id == 4:  # Motorcycle
            motorcycle_boxes.append(boxes[i])

    return np.array(car_boxes), np.array(truck_boxes), np.array(motorcycle_boxes)

def draw_boxes(image, boxes, color):
    for box in boxes:
        y1, x1, y2, x2 = box
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

def detect_vehicles(image_path,predictpath,pimg,slot):
    K.clear_session()
    # Load the image
    img_get = cv2.imread(image_path)
    img = cv2.resize(img_get, (800, 600))

    # Create the Mask R-CNN model
    config = CarConfig()
    model = MaskRCNN(mode="inference", model_dir='', config=config)
    model.load_weights('model/mask_rcnn_coco.h5', by_name=True)

    # Convert image to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    

    # Perform vehicle detection
    results = model.detect([img_rgb])
    class_ids = results[0]['class_ids']
    boxes = results[0]['rois']

    # Filter vehicle boxes
    car_boxes, truck_boxes, motorcycle_boxes = get_car_boxes(boxes, class_ids)

    # Draw bounding boxes for cars, trucks, and motorcycles
    draw_boxes(img, car_boxes, (0, 255, 0))         # Green for cars
    draw_boxes(img, truck_boxes, (255, 0, 0))      # Blue for trucks
    draw_boxes(img, motorcycle_boxes, (0, 0, 255))  # Red for motorcycles

    # Display the image with vehicle detections
    cv2.imshow('Vehicle Detections', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Print the counts of each vehicle type
    print(f"Number of cars: {len(car_boxes)}")
    print(f"Number of trucks: {len(truck_boxes)}")
    print(f"Number of motorcycles: {len(motorcycle_boxes)}")
    
    num_cars=len(car_boxes)
    num_trucks=len(truck_boxes)
    num_motorcycles = len(motorcycle_boxes)
    # Save the image with detections
    
    footer_text = f"Cars: {num_cars} | Trucks: {num_trucks} | Motorcycles: {num_motorcycles}"
    print(footer_text)
    cv2.putText(img, footer_text, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    # cv2.imwrite('predict.jpg', img)
    output_path = os.path.join(predictpath,pimg)
    cv2.imwrite(output_path, img)
    if slot == 'slot1':
        newpath='Images/predict1/'+pimg
    elif slot == 'slot2':
        newpath='Images/predict2/'+pimg
    return len(car_boxes),len(truck_boxes),len(motorcycle_boxes),newpath
    # DB_NAME = '../database/accounts.db'
    # try:
    #     con = sqlite3.connect(DB_NAME)
    #     cursor = con.cursor()
    #     cursor.execute("SELECT s1photo,s2photo FROM parking_data WHERE manager_id=?",(session['mid'],))
    #     photos = cursor.fetchone()
        
    #     if slot == 'slot1' :
    #         convert_data(photos[0], 'Static/Images/slot1/image1.jpg')
    #     elif slot == 'slot2' :
    #         convert_data(photos[1], 'Static/Images/slot2/image2.jpg')
        
    # except Exception as e:
    #     print(e)
        
    # finally:
    #     con.close()

# Path to the input image
# image_path = 'clg/3.jpg'
# image_path = 'kochi/marinedrive.JPG'

# Call the vehicle detection function
# detect_vehicles(image_path)
