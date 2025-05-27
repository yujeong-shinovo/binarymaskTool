import os
import sys
import cv2
import numpy as np
from tkinter import Tk, Canvas, NW
from PIL import Image, ImageTk, ImageDraw
from tkinter import messagebox


class MaskAnnotator:
    def __init__(self, folder_path, save_folder):
        self.folder_path = folder_path
        self.save_folder = save_folder
        self.image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.image_files.sort()
        if not self.image_files:
            messagebox.showerror("Error", "No images found in the folder.")
            sys.exit(1)

        self.idx = 0
        self.scale_factor = 2 #image size on canvas

        self.root = Tk()
        self.root.title("Mask Annotator") # change the title if you want

        self.canvas = Canvas(self.root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.root.bind("<Return>", self.save_mask)
        self.root.bind("<Left>", self.prev_image)
        self.root.bind("<Right>", self.next_image)

        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<Button-3>", self.right_click)
        self.canvas.bind("<ButtonPress-2>", self.middle_press)
        self.canvas.bind("<B2-Motion>", self.middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.middle_release)

        self.load_image()
        self.root.mainloop()

    def load_image(self):
        self.canvas.delete("all")
        self.polygon_points = []

        img_path = os.path.join(self.folder_path, self.image_files[self.idx])
        self.original_image = Image.open(img_path).convert("RGB")
        self.image = self.original_image.resize(
            (self.original_image.width * self.scale_factor, self.original_image.height * self.scale_factor)
        )
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.root.geometry(f"{self.image.width}x{self.image.height}")
        self.canvas.config(width=self.image.width, height=self.image.height)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=NW)

        self.mask = Image.new("L", self.image.size, 0)
        self.draw = ImageDraw.Draw(self.mask)

        self.redraw_mask()

    def left_click(self, event):
        if event.state & 0x0001:
            if len(self.polygon_points) < 3:
                messagebox.showwarning("Warning", "At least 3 points needed to fill polygon.")
                return
            self.draw.polygon(self.polygon_points, fill=255)
            self.redraw_mask()
            self.polygon_points = []
            self.canvas.delete("polygon")
        else:
            self.polygon_points.append((event.x, event.y))
            self.redraw_polygon()

    def right_click(self, event):
        self.polygon_points = []
        self.canvas.delete("polygon")

    def middle_press(self, event):
        self.drag_start = (event.x, event.y)
        self.drag_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", dash=(4, 2), tags="drag")

    def middle_drag(self, event):
        self.canvas.coords(self.drag_rect, self.drag_start[0], self.drag_start[1], event.x, event.y)

    def middle_release(self, event):
        x0, y0 = self.drag_start
        x1, y1 = event.x, event.y
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        self.canvas.delete("drag")
        self.apply_grabcut(x0, y0, x1, y1)

    def apply_grabcut(self, x0, y0, x1, y1):
        img_np = np.array(self.image)
        mask = np.zeros(img_np.shape[:2], np.uint8)
        rect = (x0, y0, x1 - x0, y1 - y0)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(img_np, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        except:
            return
        result_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')
        result_mask_pil = Image.fromarray(result_mask)
        self.mask.paste(result_mask_pil, (0, 0), result_mask_pil)
        self.redraw_mask()

    def redraw_polygon(self):
        self.canvas.delete("polygon")
        if len(self.polygon_points) > 1:
            self.canvas.create_line(
                *sum(self.polygon_points, ()), fill="white", width=2, tags="polygon"
            )
        for x, y in self.polygon_points:
            r = 3
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="white", outline="white", tags="polygon")

    def redraw_mask(self):
        self.canvas.delete("mask")
        mask_img = Image.new("RGBA", self.mask.size, (255, 255, 255, 0))
        alpha = self.mask.point(lambda p: 150 if p > 0 else 0)
        mask_img.putalpha(alpha)
        combined = Image.alpha_composite(self.image.convert("RGBA"), mask_img)
        self.tk_mask = ImageTk.PhotoImage(combined)
        self.canvas.create_image(0, 0, image=self.tk_mask, anchor=NW, tags="mask")

    def save_mask(self, event=None):
        final_mask = self.mask.resize(self.original_image.size, resample=Image.NEAREST)
        os.makedirs(self.save_folder, exist_ok=True)
        base_name = os.path.splitext(self.image_files[self.idx])[0]
        mask_path = os.path.join(self.save_folder, f"{base_name}.png")
        final_mask.save(mask_path)
        messagebox.showinfo("Saved", f"Mask saved as:\n{mask_path}")
        if self.idx < len(self.image_files) - 1:
            self.idx += 1
            self.load_image()
        else:
            messagebox.showinfo("Done", "All images annotated.")
            self.root.quit()

    def prev_image(self, event=None):
        if self.idx > 0:
            self.idx -= 1
            self.load_image()

    def next_image(self, event=None):
        if self.idx < len(self.image_files) - 1:
            self.idx += 1
            self.load_image()
    def left_click(self, event):
        shift_pressed = (event.state & 0x0001) != 0
        ctrl_pressed = (event.state & 0x0004) != 0

        if shift_pressed and ctrl_pressed:
            # Erase polygon area if polygon has 3+ points
            if len(self.polygon_points) < 3:
                messagebox.showwarning("Warning", "At least 3 points needed to erase polygon.")
                return
            self.draw.polygon(self.polygon_points, fill=0)  # Fill black to erase
            self.redraw_mask()
            self.polygon_points = []
            self.canvas.delete("polygon")
        elif shift_pressed:
            # Fill polygon area white as before
            if len(self.polygon_points) < 3:
                messagebox.showwarning("Warning", "At least 3 points needed to fill polygon.")
                return
            self.draw.polygon(self.polygon_points, fill=255)
            self.redraw_mask()
            self.polygon_points = []
            self.canvas.delete("polygon")
        else:
            self.polygon_points.append((event.x, event.y))
            self.redraw_polygon()


if __name__ == "__main__":
    import argparse
    base_path = "path/of/dataset"
    parser = argparse.ArgumentParser(description="binarymaskgenerator")
    parser.add_argument("--category", required=True, help="name of category") # for the case of multiple category under dataset folder. change each dir path or parser if needed.
    args = parser.parse_args()
    source_dir = os.path.join(base_path, args.category, "abnormal_dir") #name of data directory 
    target_dir = os.path.join(base_path, args.category, "mask_dir") # name of directory to save mask

    MaskAnnotator(source_dir, target_dir)
