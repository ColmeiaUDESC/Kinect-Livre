"""Seleção de quatro cantos sobre a imagem de profundidade do Kinect."""
import math
import tkinter as tk


def validate_area(points):
    if not points:
        return
    if len(points) != 4 or any(len(p) != 2 for p in points):
        raise ValueError("Marque os quatro cantos da caixa antes de aplicar.")
    if not all(math.isfinite(v) and 0 <= v <= 1 for p in points for v in p):
        raise ValueError("Os cantos precisam ficar dentro da imagem de profundidade.")
    crosses = []
    area = 0
    for i, (x, y) in enumerate(points):
        bx, by = points[(i + 1) % 4]
        cx, cy = points[(i + 2) % 4]
        crosses.append((bx-x)*(cy-by)-(by-y)*(cx-bx))
        area += x*by-bx*y
    if (any(abs(c) < 1e-6 for c in crosses)
            or any(c*crosses[0] <= 0 for c in crosses)):
        raise ValueError("Marque os cantos em volta da caixa, sem cruzar as linhas.")
    if abs(area) < .01:
        raise ValueError("A área ficou muito pequena. Marque as bordas internas da caixa.")


class SensorCanvas(tk.Canvas):
    """Image and editable polygon use the same fitted coordinate transform."""
    def __init__(self, parent, changed, **kwargs):
        self.raw_image = self.display_image = None
        self.message = "Clique em Aplicar para iniciar o sensor."
        self.points = []
        self.editable = False
        self.drag = None
        self.changed = changed
        self.image_rect = None
        self.scale_key = None
        super().__init__(parent, bg="black", highlightthickness=0, height=160, **kwargs)
        self.bind("<Configure>", lambda event: self.redraw())
        self.bind("<Button-1>", self.press)
        self.bind("<B1-Motion>", self.move)
        self.bind("<ButtonRelease-1>", lambda event: setattr(self, "drag", None))

    def configure(self, cnf=None, **kwargs):
        if "image" in kwargs:
            self.raw_image = kwargs.pop("image") or None
            self.scale_key = None
        if "text" in kwargs:
            self.message = kwargs.pop("text")
        result = super().configure(cnf, **kwargs) if cnf is not None or kwargs else None
        self.redraw()
        return result

    config = configure

    def cget(self, key):
        if key == "text":
            return self.message
        return super().cget(key)

    def redraw(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        self.image_rect = None
        if self.raw_image is None:
            self.create_text(width/2, height/2, text=self.message, fill="white",
                             width=max(100, width-24))
            return
        iw, ih = self.raw_image.width(), self.raw_image.height()
        # Small integer scaling fits the entire image even in an 800x600 desktop.
        numerator = max(1, min(8, int(min(width/iw, height/ih)*4)))
        key = (str(self.raw_image), numerator)
        if key != self.scale_key:
            self.display_image = self.raw_image.zoom(numerator).subsample(4)
            self.scale_key = key
        dw, dh = self.display_image.width(), self.display_image.height()
        left, top = (width-dw)/2, (height-dh)/2
        self.image_rect = (left, top, dw, dh)
        self.create_image(left, top, anchor="nw", image=self.display_image)
        if self.editable and self.points:
            coords = [(left+x*dw, top+y*dh) for x, y in self.points]
            if len(coords) == 4:
                self.create_polygon(*[v for p in coords for v in p], fill="", outline="#00ff88", width=2)
            elif len(coords) > 1:
                self.create_line(*[v for p in coords for v in p], fill="#00ff88", width=2)
            for i, (x, y) in enumerate(coords):
                self.create_oval(x-5,y-5,x+5,y+5,fill="#00ff88",outline="black")
                self.create_text(x+10,y+10,text=str(i+1),fill="#00ff88",anchor="nw")

    def image_point(self, x, y, clamp=False):
        if not self.image_rect:
            return None
        left, top, width, height = self.image_rect
        u, v = (x-left)/width, (y-top)/height
        if not clamp and not (0 <= u <= 1 and 0 <= v <= 1):
            return None
        return [max(0, min(1, u)), max(0, min(1, v))]

    def press(self, event):
        if not self.editable or self.raw_image is None:
            return
        point = self.image_point(event.x, event.y)
        if point is None:
            return
        _, _, width, height = self.image_rect
        for i, (x, y) in enumerate(self.points):
            if math.hypot((x-point[0])*width, (y-point[1])*height) < 14:
                self.drag = i
                return
        if len(self.points) < 4:
            self.points.append(point)
            self.drag = len(self.points)-1
            self.changed(self.points)
            self.redraw()

    def move(self, event):
        if self.editable and self.drag is not None and self.raw_image is not None:
            self.points[self.drag] = self.image_point(event.x, event.y, clamp=True)
            self.changed(self.points)
            self.redraw()
