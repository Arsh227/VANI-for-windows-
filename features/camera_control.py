import cv2
import time
import os
from datetime import datetime
import numpy as np

class CameraControl:
    def __init__(self):
        self.camera = None
        self.is_recording = False
        self.output_dir = "camera_output"
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def initialize_camera(self):
        """Initialize camera if not already initialized"""
        try:
            if self.camera is None:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise Exception("Could not open camera")
            return True
        except Exception as e:
            print(f"Camera initialization error: {e}")
            return False

    def take_photo(self):
        """Take a photo with image enhancement"""
        try:
            if not self.initialize_camera():
                return "Camera not available"
                
            # Take photo
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Could not capture frame")
                
            # Convert to numpy array for processing
            frame = np.array(frame)
            # Enhance image
            frame = np.clip(frame * 1.2, 0, 255).astype('uint8')
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"photo_{timestamp}.jpg")
            
            # Save photo
            cv2.imwrite(filename, frame)
            
            return f"Photo saved as {filename}"
            
        except Exception as e:
            print(f"Photo error: {e}")
            return "Error taking photo"
        finally:
            self.release_camera()

    def start_recording(self):
        """Start video recording"""
        try:
            if not self.initialize_camera():
                return "Camera not available"
                
            if self.is_recording:
                return "Already recording"
                
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"video_{timestamp}.avi")
            
            # Get video properties
            frame_width = int(self.camera.get(3))
            frame_height = int(self.camera.get(4))
            
            # Initialize video writer
            self.video_writer = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*'XVID'),
                20.0, (frame_width, frame_height)
            )
            
            self.is_recording = True
            return "Started recording"
            
        except Exception as e:
            print(f"Recording start error: {e}")
            return "Error starting recording"

    def stop_recording(self):
        """Stop video recording"""
        try:
            if not self.is_recording:
                return "Not recording"
                
            self.is_recording = False
            self.video_writer.release()
            return "Recording stopped"
            
        except Exception as e:
            print(f"Recording stop error: {e}")
            return "Error stopping recording"
        finally:
            self.release_camera()

    def release_camera(self):
        """Release camera resources"""
        try:
            if self.camera is not None:
                self.camera.release()
                self.camera = None
        except Exception as e:
            print(f"Camera release error: {e}") 