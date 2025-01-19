import sys
import os
import io
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard, QImage, QPixmap
from PIL import Image, ImageDraw, ImageFont

class ImageDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Dimensions Viewer")
        self.setMinimumSize(300, 200)
        
        # Create label for displaying dimensions
        self.label = QLabel("Drop an image here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)
        
        # Enable drop events
        self.setAcceptDrops(True)
        
        # Store clipboard reference
        self.clipboard = QApplication.clipboard()
    
    def calculate_scale_factors(self, img_width, img_height):
        # Base scale on the smaller dimension to ensure overlay fits
        min_dimension = min(img_width, img_height)
        
        # Scale factors for different image sizes
        if min_dimension <= 500:  # Small images
            scale = 0.15
        elif min_dimension <= 1000:  # Medium images
            scale = 0.1
        elif min_dimension <= 2000:  # Large images
            scale = 0.06
        else:  # Very large images
            scale = 0.04
        
        # Calculate font size (min 16px, max 48px)
        font_size = max(16, min(48, int(min_dimension * scale)))
        
        # Calculate padding and border thickness based on font size
        padding = max(10, int(font_size * 0.6))
        border_thickness = max(2, int(font_size * 0.08))
        
        # Calculate bottom margin as percentage of height
        bottom_margin = int(img_height * 0.03)  # 3% of image height
        
        return {
            'font_size': font_size,
            'padding': padding,
            'border_thickness': border_thickness,
            'bottom_margin': bottom_margin
        }
    
    def add_dimensions_overlay(self, image_path, dimensions):
        # Open image and create draw object
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Calculate scale factors based on image size
        scale = self.calculate_scale_factors(img.width, img.height)
        
        # Try to get system monospace font, fallback to default
        try:
            # Try SF Mono first, then Monaco as fallback
            try:
                font = ImageFont.truetype("/System/Library/Fonts/SFMono-Regular.otf", scale['font_size'])
            except:
                font = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", scale['font_size'])
        except:
            font = ImageFont.load_default()
        
        # Prepare text
        text = f"{dimensions} pixels"
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position (bottom center)
        x = (img.width - text_width) // 2
        y = img.height - text_height - scale['bottom_margin']
        
        # Add black background with red border
        padding = scale['padding']
        background_bbox = [
            x - padding,
            y - padding,
            x + text_width + padding,
            y + text_height + padding
        ]
        # Draw black background
        draw.rectangle(background_bbox, fill='black')
        # Draw red border
        for offset in range(scale['border_thickness']):
            border_bbox = [
                background_bbox[0] - offset,
                background_bbox[1] - offset,
                background_bbox[2] + offset,
                background_bbox[3] + offset
            ]
            draw.rectangle(border_bbox, fill=None, outline='red')
        
        # Draw white text
        draw.text((x, y), text, fill='white', font=font)
        
        # Convert PIL image to QImage for clipboard
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qimg = QImage.fromData(buffer.getvalue())
        
        return qimg
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        files = event.mimeData().urls()
        if files:
            image_path = files[0].toLocalFile()
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    dimensions = f"{width} × {height}"
                    
                    # Add dimensions overlay and copy to clipboard
                    modified_image = self.add_dimensions_overlay(image_path, dimensions)
                    self.clipboard.setImage(modified_image)
                    
                    # Update label with "copied" message
                    self.label.setText(f"{dimensions} pixels\nImage with overlay copied to clipboard")
                    
            except Exception as e:
                self.label.setText(f"Error: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ImageDropWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 