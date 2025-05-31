from sys import flags
import time
import cv2
import pyautogui as p

def find_working_camera():
    for i in range(2):  # Try first two camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            return cap
    return None

def AuthenticateFace():
    flag = 0  # Initialize flag with 0 (authentication failed)

    # Local Binary Patterns Histograms
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read('BRAIN/auth/trainer/trainer.yml')  # load trained model
    cascadePath = "BRAIN/auth/haarcascade_frontalface_default.xml"
    # initializing haar cascade for object detection approach
    faceCascade = cv2.CascadeClassifier(cascadePath)

    font = cv2.FONT_HERSHEY_SIMPLEX  # denotes the font type

    id = 2  # number of persons you want to Recognize

    names = ['', 'Aman Hingve']  # Added 'Unknown' as fallback

    # Initialize camera
    cam = find_working_camera()
    if cam is None:
        print("Error: No working camera found. Please check your camera connection.")
        return flag

    cam.set(3, 640)  # set video FrameWidht
    cam.set(4, 480)  # set video FrameHeight

    # Define min window size to be recognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    while True:
        ret, img = cam.read()  # read the frames using the above created object
        if not ret:
            print("Error: Could not read frame")
            break

        # The function converts an input image from one color space to another
        converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            converted_image,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        for(x, y, w, h) in faces:

            # used to draw a rectangle on any image
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # to predict on every single image
            id_pred, accuracy = recognizer.predict(converted_image[y:y+h, x:x+w])

            # Ensure id_pred is within valid range
            if id_pred < 0 or id_pred >= len(names):
                id_name = "Unknown"
                flag = 0
            else:
                if accuracy < 100:
                    id_name = names[id_pred]
                    accuracy = "  {0}%".format(round(100 - accuracy))
                    flag = 1
                else:
                    id_name = "Unknown"
                    accuracy = "  {0}%".format(round(100 - accuracy))
                    flag = 0

            cv2.putText(img, str(id_name), (x+5, y-5), font, 1, (255, 255, 255), 2)
            cv2.putText(img, str(accuracy), (x+5, y+h-5),
                        font, 1, (255, 255, 0), 1)

        cv2.imshow('camera', img)

        k = cv2.waitKey(10) & 0xff  # Press 'ESC' for exiting video
        if k == 27:
            break
        if flag == 1:
            break

    # Do a bit of cleanup
    cam.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    return flag

# if __name__ == "__main__":
#     AuthenticateFace()