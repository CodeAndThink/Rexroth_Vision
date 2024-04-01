import gi
import datetime
import cv2
import os
import numpy
import numpy as np
import pytesseract
from PIL import Image

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib

class Demo_vision_app:
    def __init__(self):
        self.ImageURL = ""
        self.builder = Gtk.Builder()
        self.builder.add_from_file("Demo_vision_app.glade")

        self.empty_image_URL = "default_icons/Image_Empty.png"
        self.start_time = datetime.datetime.now()

        # Lấy các đối tượng từ Glade
        self.window = self.builder.get_object("MainScreen")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_default_size(800, 600)

        self.InputBtn = self.builder.get_object("InputImage")
        self.InputBtn.connect("clicked", self.on_InputImage_clicked)

        self.SaveBtn = self.builder.get_object("SaveImage")
        self.SaveBtn.connect("clicked", self.on_SaveImage_clicked)

        self.RemoveBtn = self.builder.get_object("RemoveImage")
        self.RemoveBtn.connect("clicked", self.on_RemoveImage_clicked)

        self.RealtimeLabel = self.builder.get_object("RealtimeLabel")
        self.AppRuntime = self.builder.get_object("AppRuntime")

        self.ScreenImage = self.builder.get_object("ScreenImage")

        self.TextCaptureBox = self.builder.get_object("TextCaptureBox")

        # Tạo một GtkScrolledWindow
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.OptionImage = self.builder.get_object("OptionImage")
        self.OptionImage.set_label("Options")

        self.ScaleCtrl = self.builder.get_object("ScaleCtrl")
        self.ScaleCtrl.set_range(0.1, 2)  # Thiết lập phạm vi giá trị
        self.ScaleCtrl.set_value(1)  # Thiết lập giá trị ban đầu
        self.ScaleCtrl.connect("value-changed", self.on_scale_changed)  # Kết nối sự kiện

        # Tạo một Gtk.Menu
        self.menu = Gtk.Menu()

        self.CropOption = Gtk.MenuItem(label="Crop")
        self.ResizeOption = Gtk.MenuItem(label="Resize")
        self.BackRemoveOption = Gtk.MenuItem(label="Remove Background")
        self.TextCapture = Gtk.MenuItem(label="Get Text")
        self.CurveDetect = Gtk.MenuItem(label="Detect Object Curve")

        self.menu.append(self.CropOption)
        self.menu.append(self.ResizeOption)
        self.menu.append(self.BackRemoveOption)
        self.menu.append(self.TextCapture)
        self.menu.append(self.CurveDetect)

        self.CropOption.connect("activate", self.on_CropImage_clicked)
        self.ResizeOption.connect("activate", self.on_ResizeImage_clicked)
        self.BackRemoveOption.connect("activate", self.on_BackRemove_clicked)
        self.TextCapture.connect("activate", self.on_TextCapture_clicked)
        self.CurveDetect.connect("activate", self.on_CurveDetect_clicked)

        self.menu.show_all()
        self.OptionImage.set_popup(self.menu)

        # Gán menu cho nút Gtk.MenuButton
        GLib.timeout_add_seconds(1, self.update_time)
    def on_BackRemove_clicked(self, widget):
        # Lấy pixbuf từ Gtk.Image
        if self.ImageURL is None:
            print("Không có ảnh được hiển thị.")
        else:
            img = cv2.imread(self.ImageURL)

            #threshold on white
            #define lower and upper limits
            lower = np.array([200, 200, 200])
            upper = np.array([255, 255, 255])

            #create mask to only select black
            thresh = cv2.inRange(img, lower, upper)

            #apply morphology
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            #invest morp image
            mask = 255 - morph

            #apply mask to image
            result = cv2.bitwise_and(img, img, mask = mask)

            # Chuyển đổi ảnh xử lý trở lại GdkPixbuf
            height, width, _ = result.shape
            data = result.tobytes()

            pixbuf = GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, width, height, width * 3)
            # Cập nhật Gtk.Image với ảnh đã xử lý
            self.ScreenImage.set_from_pixbuf(pixbuf)
    def on_TextCapture_clicked(self, widget):
        image = cv2.imread(self.ImageURL)

        # threshold on white
        # define lower and upper limits
        lower = np.array([200, 200, 200])
        upper = np.array([255, 255, 255])

        # create mask to only select black
        thresh = cv2.inRange(image, lower, upper)
        # Chuyển đổi hình ảnh sang ảnh xám để phát hiện văn bản
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Phát hiện văn bản trong ảnh
        text_boxes = pytesseract.image_to_boxes(thresh)
        text = pytesseract.image_to_string(gray_image)

        # Vẽ các hộp giới hạn của văn bản lên ảnh gốc
        for box in text_boxes.splitlines():
            box = box.split()
            x, y, w, h = int(box[1]), int(box[2]), int(box[3]), int(box[4])
            cv2.rectangle(image, (x, y), (w, h), (0, 255, 0), 2)

        # Hiển thị ảnh đã phát hiện văn bản lên Gtk Image
        self.display_image(image)
        self.TextCaptureBox.set_text(image)
    def on_CurveDetect_clicked(self, widget):
        # Đọc ảnh
        image = cv2.imread(self.ImageURL)

        # Chuyển đổi ảnh sang ảnh xám
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Làm mờ ảnh để giảm nhiễu
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Phát hiện biên cạnh bằng phương pháp Canny
        edged = cv2.Canny(blurred, 30, 150)

        # Tìm contours trong ảnh
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Vẽ các contours lên ảnh gốc
        cv2.drawContours(image, contours, -1, (0, 255, 0), 2)
        self.display_image(image)
    def display_image(self, image):
        # Chuyển đổi hình ảnh từ OpenCV sang GdkPixbuf
        height, width, channels = image.shape

        # Chuyển đổi ảnh sang định dạng PNG
        retval, buffer = cv2.imencode('.png', image)
        if not retval:
            print("Could not encode image to PNG format")
            return

        # Chuyển đổi buffer thành chuỗi bytes
        data = buffer.tobytes()

        # Tạo GdkPixbuf từ dữ liệu bytes
        loader = GdkPixbuf.PixbufLoader.new_with_type('png')
        loader.write(data)
        loader.close()

        gdkpixbuf = loader.get_pixbuf()

        # Hiển thị hình ảnh lên Gtk Image
        self.ScreenImage.set_from_pixbuf(gdkpixbuf)

        # Đọc văn bản từ ảnh và hiển thị nó trên Gtk Label
        recognized_text = pytesseract.image_to_string(image)
        self.TextCaptureBox.set_text(recognized_text)

    def perform_ocr(self, image_path):
        # Sử dụng pytesseract để nhận dạng chữ từ ảnh
        image = Image.open(image_path)
        recognized_text = pytesseract.image_to_string(image)
        return recognized_text
    def on_CropImage_clicked(self):
        return
    def on_ResizeImage_clicked(self):
        return
    def update_time(self):
        # Lấy thời gian hiện tại
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.RealtimeLabel.set_text(current_time)

        elapsed_time = datetime.datetime.now() - self.start_time
        seconds = elapsed_time.total_seconds()

        # Chuyển đổi thời gian sang giờ, phút và giây
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Tạo chuỗi để hiển thị
        if hours > 0:
            time_string = "{}h {}m {}s".format(int(hours), int(minutes), int(seconds))
        elif minutes > 0:
            time_string = "{}m {}s".format(int(minutes), int(seconds))
        else:
            time_string = "{}s".format(int(seconds))

        # Cập nhật label với thời gian đã trôi qua
        self.AppRuntime.set_text(time_string)
        return True
    def on_InputImage_clicked(self, button):
        dialog = Gtk.FileChooserDialog(title="Image Selection", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        # Hiển thị hộp thoại và chờ người dùng chọn
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Lấy đường dẫn của tập tin được chọn
            filename = dialog.get_filename()
            print("Select: ", filename)
            self.ImageURL = filename
            self.load_image(filename)
            dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel Image Selection")
            # Đóng hộp thoại
            dialog.destroy()
    def load_image(self, filename):
        original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        # Lấy kích thước của GtkImage
        image_width = self.ScreenImage.get_allocated_width()
        image_height = self.ScreenImage.get_allocated_height()

        # Kiểm tra kích thước của ảnh
        if image_width > 0 and image_height > 0:
            image_ratio = image_width/image_height
            picture_ratio = original_pixbuf.get_width() / original_pixbuf.get_height();
            if image_ratio > picture_ratio:
                scaled_pixbuf = original_pixbuf.scale_simple(
                    int(picture_ratio * image_height),
                    image_height,
                    GdkPixbuf.InterpType.BILINEAR
                )
            else:
                scaled_pixbuf = original_pixbuf.scale_simple(
                    image_width,
                    int(image_width/picture_ratio),
                    GdkPixbuf.InterpType.BILINEAR
                )
            self.ScreenImage.set_from_pixbuf(scaled_pixbuf)
        else:
            print("Kích thước ảnh không hợp lệ")
    def on_RemoveImage_clicked(self, widget):
        self.ScreenImage.clear()
        self.TextCaptureBox.set_text("")
    def on_SaveImage_clicked(self, widget):
        pixbuf = self.ScreenImage.get_pixbuf()
        if pixbuf is not None:
            # Hiển thị hộp thoại lưu tệp và chờ người dùng chọn
            dialog = Gtk.FileChooserDialog(
                title="Save Image",
                parent=self.window,
                action=Gtk.FileChooserAction.SAVE,
                buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )
            dialog.set_current_name("image.jpg")

            # Lấy đường dẫn tệp đã chọn
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                save_filename = dialog.get_filename()
                dialog.destroy()

                # Lưu ảnh ra file
                pixbuf.savev(save_filename, "jpeg", [], [])
                print("Image saved as:", save_filename)
            else:
                dialog.destroy()
        else:
            print("No image to save.")
    def on_scale_changed(self, scale):
        original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.ImageURL)
        if self.ImageURL is not None:
            # Lấy giá trị từ thanh điều chỉnh
            scale_factor = scale.get_value()
            height = original_pixbuf.get_height()
            width = original_pixbuf.get_width()
            # Tạo ảnh mới với kích thước thay đổi dựa trên tỷ lệ
            new_height = int(height * scale_factor)
            new_width = int(width * scale_factor)
            scaled_pixbuf = original_pixbuf.scale_simple(
                new_width,
                new_height,
                GdkPixbuf.InterpType.BILINEAR
            )
            self.ScreenImage.set_from_pixbuf(scaled_pixbuf)
        else:
            print("No image")
    def run(self):
        # Gọi phương thức run() của Gtk.Application
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = Demo_vision_app()
    app.run()
