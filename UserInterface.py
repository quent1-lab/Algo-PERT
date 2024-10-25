import pygame as pg

class Button:
    def __init__(self, function_clicked, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.clicked = False
    
    def is_hover(self, mouse_pos: tuple[float, float]) -> bool:
        x, y = mouse_pos
        return x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height

    def click(self, click: bool, mouse_pos: tuple[float, float]):
        if click:
            if self.is_hover(mouse_pos):
                self.clicked = True
        else:
            self.clicked = False


BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

hot_bar = Button(lambda: None, 0, 0, 0, 40)
button_mode = Button(lambda: print("None."), 0, 0, 100, 30)
button_screen = Button(lambda: print("None."), 100, 0, 100, 30)


def button_core(surface: pg.Surface, text: str, button: Button):
    pg.draw.rect(surface, GRAY, pg.Rect(button.x, button.y, button.width, button.height))
    txt = font.render(text, True, BLACK)
    surface.blit(txt, (button.x + 5, button.y + 5))

def render_interface(surface: pg.Surface, mouse_pos: tuple[int, int], clicked: bool):
    global font
    font = pg.font.Font(None, int(24))

    if hot_bar.is_hover(mouse_pos): # Render the hotbar.
        button_core(surface, "VIEW", button_mode)
        button_core(surface, "SCREEN", button_screen)
    
    button_mode.click(clicked, mouse_pos)
    button_screen.click(clicked, mouse_pos)

