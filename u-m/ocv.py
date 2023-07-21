import cv2
import numpy as np
import yaml


class CaptureReadError(Exception):
    pass


class CoordinatesGenerator:
    KEY_RESET = ord("r")
    KEY_QUIT = ord("q")

    def __init__(self, image, output, color):
        self.output = output
        self.caption = image
        self.color = color

        self.image = cv2.imread(image).copy()
        self.click_count = 0
        self.ids = 0
        self.coordinates = []

        cv2.namedWindow(self.caption, cv2.WINDOW_GUI_EXPANDED)
        cv2.setMouseCallback(self.caption, self.__mouse_callback)

    def generate(self):
        while True:
            cv2.imshow(self.caption, self.image)
            key = cv2.waitKey(0)

            if key == CoordinatesGenerator.KEY_RESET:
                self.image = self.image.copy()
            elif key == CoordinatesGenerator.KEY_QUIT:
                break
        cv2.destroyWindow(self.caption)

    def __mouse_callback(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.coordinates.append((x, y))
            self.click_count += 1

            if self.click_count >= 4:
                self.__handle_done()

            elif self.click_count > 1:
                self.__handle_click_progress()

        cv2.imshow(self.caption, self.image)

    def __handle_click_progress(self):
        cv2.line(self.image, self.coordinates[-2], self.coordinates[-1], (255, 0, 0), 1)

    def __handle_done(self):
        cv2.line(self.image,
                 self.coordinates[2],
                 self.coordinates[3],
                 self.color,
                 1)
        cv2.line(self.image,
                 self.coordinates[3],
                 self.coordinates[0],
                 self.color,
                 1)

        self.click_count = 0

        coordinates = np.array(self.coordinates)

        self.output.write("-\n          id: " + str(self.ids) + "\n          coordinates: [" +
                          "[" + str(self.coordinates[0][0]) + "," + str(self.coordinates[0][1]) + "]," +
                          "[" + str(self.coordinates[1][0]) + "," + str(self.coordinates[1][1]) + "]," +
                          "[" + str(self.coordinates[2][0]) + "," + str(self.coordinates[2][1]) + "]," +
                          "[" + str(self.coordinates[3][0]) + "," + str(self.coordinates[3][1]) + "]]\n")

        draw_contours(self.image, coordinates, str(self.ids + 1), (255, 255, 255))

        for i in range(0, 4):
            self.coordinates.pop()

        self.ids += 1


class MotionDetector:
    LAPLACIAN = 1.4
    DETECT_DELAY = 1

    def __init__(self, video, coordinates, start_frame):
        self.video = video
        self.coordinates_data = coordinates
        self.start_frame = start_frame
        self.contours = []
        self.bounds = []
        self.mask = []
        self.occupied_count = 0
        self.empty_count = 0

    def detect_motion(self):
        capture = cv2.VideoCapture(self.video)
        capture.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

        coordinates_data = self.coordinates_data

        for p in coordinates_data:
            coordinates = np.array(p["coordinates"])

            rect = cv2.boundingRect(coordinates)

            new_coordinates = coordinates.copy()
            new_coordinates[:, 0] = coordinates[:, 0] - rect[0]
            new_coordinates[:, 1] = coordinates[:, 1] - rect[1]

            self.contours.append(coordinates)
            self.bounds.append(rect)

            mask = cv2.drawContours(
                np.zeros((rect[3], rect[2]), dtype=np.uint8),
                [new_coordinates],
                contourIdx=-1,
                color=255,
                thickness=-1,
                lineType=cv2.LINE_8)

            mask = mask == 255
            self.mask.append(mask)

        statuses = [False] * len(coordinates_data)
        times = [None] * len(coordinates_data)

        while capture.isOpened():
            result, frame = capture.read()
            if frame is None:
                break

            if not result:
                raise CaptureReadError("Error reading video capture on frame %s" % str(frame))

            blurred = cv2.GaussianBlur(frame.copy(), (5, 5), 3)
            grayed = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            new_frame = frame.copy()

            position_in_seconds = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            for index, c in enumerate(coordinates_data):
                status = self.__apply(grayed, index, c)

                if times[index] is not None and self.same_status(statuses, index, status):
                    times[index] = None
                    continue

                if times[index] is not None and self.status_changed(statuses, index, status):
                    if position_in_seconds - times[index] >= MotionDetector.DETECT_DELAY:
                        statuses[index] = status
                        times[index] = None
                    continue

                if times[index] is None and self.status_changed(statuses, index, status):
                    times[index] = position_in_seconds

            for index, p in enumerate(coordinates_data):
                coordinates = np.array(p["coordinates"])

                color = (0, 255, 0) if statuses[index] else (0, 0, 255)
                draw_contours(new_frame, coordinates, str(p["id"] + 1), (255, 255, 255), color)

            self.occupied_count = sum(statuses)
            self.empty_count = len(statuses) - self.occupied_count

            # Add footer information
            footer_text = f"Occupied: {self.empty_count}, Empty: {self.occupied_count}"
            cv2.putText(new_frame, footer_text, (10, new_frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            cv2.imshow(str(self.video), new_frame)
            k = cv2.waitKey(1)
            if k == ord("q"):
                break

        capture.release()
        cv2.destroyAllWindows()

        # Save the final detection image
        output_image_file = "Static/Video/Video_predict/detection_image.jpg"
        cv2.imwrite(output_image_file, new_frame)
        print(f"Detection image saved: {output_image_file}")

    def __apply(self, grayed, index, p):
        coordinates = np.array(p["coordinates"])

        rect = self.bounds[index]

        roi_gray = grayed[rect[1]:(rect[1] + rect[3]), rect[0]:(rect[0] + rect[2])]
        laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)

        coordinates[:, 0] = coordinates[:, 0] - rect[0]
        coordinates[:, 1] = coordinates[:, 1] - rect[1]

        status = np.mean(np.abs(laplacian * self.mask[index])) < MotionDetector.LAPLACIAN

        return status

    @staticmethod
    def same_status(coordinates_status, index, status):
        return status == coordinates_status[index]

    @staticmethod
    def status_changed(coordinates_status, index, status):
        return status != coordinates_status[index]


def draw_contours(image, coordinates, label, font_color, border_color=(255, 0, 0), line_thickness=1,
                  font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=0.5):
    cv2.drawContours(image, [coordinates], contourIdx=-1, color=border_color,
                     thickness=2, lineType=cv2.LINE_8)
    moments = cv2.moments(coordinates)

    center = (int(moments["m10"] / moments["m00"]) - 3,
              int(moments["m01"] / moments["m00"]) + 3)

    cv2.putText(image, label, center, font, font_scale, font_color,
                line_thickness, cv2.LINE_AA)


def perform_detection(video_file, data_file, start_frame):
    capture = cv2.VideoCapture(video_file)
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_count = 0

    while capture.isOpened():
        result, frame = capture.read()
        if frame is None:
            break

        if not result:
            raise CaptureReadError("Error reading video capture on frame %s" % str(frame))

        if frame_count == 3:
            cv2.imwrite("Static/Video/Video_predict/captured_frame.jpg", frame)
            break

        frame_count += 1

    capture.release()

    image_file = "Static/Video/Video_predict/captured_frame.jpg"

    with open(data_file, "w+") as points:
        generator = CoordinatesGenerator(image_file, points, (255, 0, 0))
        generator.generate()

    with open(data_file, "r") as data:
        points = yaml.load(data, Loader=yaml.Loader)
        detector = MotionDetector(video_file, points, int(start_frame))
        detector.detect_motion()
        
        count_occupy = detector.occupied_count
        count_empty = detector.empty_count

        return count_occupy, count_empty



# video_file = "videos/parking_lot_1.mp4"
# data_file = "data/coordinates_2.yml"
# start_frame = 400

# pd = perform_detection(video_file, data_file, start_frame)
# print(pd)