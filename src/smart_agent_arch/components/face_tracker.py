import os
import pickle
from pathlib import Path

try:
    import cv2
    import numpy as np
    import face_recognition
except ImportError:
    cv2 = None
    np = None
    face_recognition = None

from smart_agent_arch.tools_loader import export_tool

class FaceMemoryTracker:
    """
    Component 2: Face Tracker & Identifier.
    Remembers new faces by assigning integer indices (0, 1, 2...).
    Draws bounding boxes around recognized old faces and new faces.
    Stores and manages face encodings between runs.
    """
    
    def __init__(self, memory_file="agent_face_memory.pkl", tolerance=0.5):
        self.memory_file = memory_file
        self.tolerance = tolerance
        # List of lists: self.known_face_encodings[index] = [encoding1, encoding2...]
        self.known_face_encodings = []
        
        self.is_ready = bool(cv2 and np and face_recognition)
        if self.is_ready:
            self._load_memory()

    def _load_memory(self):
        if Path(self.memory_file).exists():
            try:
                with open(self.memory_file, 'rb') as f:
                    self.known_face_encodings = pickle.load(f)
            except Exception as e:
                print(f"Failed to load face memory {self.memory_file}: {e}")

    def _save_memory(self):
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(self.known_face_encodings, f)
        except Exception as e:
            print(f"Failed to save face memory: {e}")

    @export_tool
    def track_and_label_faces(self, image_path: str, output_path: str = None) -> str:
        """
        Analyzes an image, assigns new mathematical indices to unknown faces, draws bounding boxes
        with their assigned IDs (0, 1, 2...) for known faces, and saves the annotated image.
        :param image_path: The path to the input image file.
        :param output_path: Optional path to save the annotated image. If empty, uses '<original>-annotated.jpg'
        :return: A JSON-like string detailing the face IDs discovered or recognized, and the output path.
        """
        if not self.is_ready:
            return "Error: Face tracker requires packages. Run: pip install opencv-python numpy face_recognition"

        if not Path(image_path).exists():
            return f"Error: Image {image_path} not found."

        # Load the image
        img = face_recognition.load_image_file(image_path)
        # Convert to BGR for OpenCV
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Detect faces
        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        found_ids = []
        memory_updated = False

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            match_index = -1
            
            # Compare with our memory list
            if self.known_face_encodings:
                # We take the mean encoding of each cluster for comparison
                averages = [np.mean(enc_list, axis=0) for enc_list in self.known_face_encodings]
                
                # Check distances
                face_distances = face_recognition.face_distance(averages, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if face_distances[best_match_index] <= self.tolerance:
                    match_index = int(best_match_index)

            # If no match found, create a new cluster
            if match_index == -1:
                match_index = len(self.known_face_encodings)
                self.known_face_encodings.append([face_encoding])
                memory_updated = True
            else:
                # Add this encoding to improve cluster accuracy over time
                self.known_face_encodings[match_index].append(face_encoding)
                memory_updated = True
            
            found_ids.append(match_index)

            # Draw highly visible bounding box and index text
            cv2.rectangle(img_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw label background
            font = cv2.FONT_HERSHEY_DUPLEX
            text = f"ID: {match_index}"
            (text_width, text_height), _ = cv2.getTextSize(text, font, 0.7, 1)
            cv2.rectangle(img_bgr, (left, bottom - text_height - 10), (left + text_width + 10, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(img_bgr, text, (left + 5, bottom - 5), font, 0.7, (0, 0, 0), 1)

        # Save memory and annotated image
        if memory_updated:
            self._save_memory()

        if not output_path:
            p = Path(image_path)
            output_path = str(p.parent / f"{p.stem}-annotated.jpg")

        cv2.imwrite(output_path, img_bgr)
        
        return f"Successfully processed image. Found {len(found_ids)} faces. IDs present: {found_ids}. Annotated image saved to: {output_path}"

