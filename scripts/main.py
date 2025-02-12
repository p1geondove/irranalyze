import pygame
import os
from time import perf_counter_ns
from math import ceil
import ntimer
from itertools import groupby
import numpy as np

def lerp(a:float, b:float, t:float) -> float:
    return a + (b - a) * t

def char_to_color(char:int) -> pygame.Color:
    """maps the raw bytes to greysale pygame colors
    
    The integers in unicode are at position 48.
    So substracting 48 from the raw input results in the actual values.
    These can be lerped to 0-255 and return a pygame.color object.
    If the input is not a number it gets mapped to red.

    Args:
        char (int): raw text encoded utf8

    Returns:
        pygame.Color: greyscale color
    """
    if char in range(48,59):
        return pygame.Color([lerp(0,255,(char-48)/9)]*3)
    else:
        return pygame.Color('red')

class Numbir:
    """big number file interface

    Used to interface big files.
    Data is read in chunks and cached for faster interface
    It provides a several stream: direct-file, utf8, int, color

    Args:
        file_path (str): the location of the file
    """
    def __init__(self, file_path:str):
        self.file_path = file_path
        self.window = (0,0)
        self.chars:dict[int|int] = {}
        self.amt_chars = os.path.getsize(self.file_path)

        self.get(0, 2**16)

    @ntimer.timer
    def get(self, start:int, end:int) -> bytes:
        def _get_file(start, end):
            chars = b""
            try:
                with open(self.file_path, "rb") as f:
                    f.seek(start)
                    chars = f.read(end - start)
            except Exception as e:
                print(f'Error reading file\nFile: {self.file_path}\nstart: {start}\nend: {end}\nError: {e}')
            finally:
                return chars

        def _put_cache(chars:bytes, start:int):
            for idx, char in enumerate(chars, start):
                self.chars[idx] = char

        def _get_cache(start:int, end:int):
            return [self.chars[x] for x in range(start,min(end,self.amt_chars))]

        def bool_chunks(bool_array:list[bool]) -> list[range]: # dont touch
            ranges = []
            start = None
            
            for idx, value in enumerate(bool_array):
                if not value and start is None:
                    start = idx
                elif value and start is not None:
                    ranges.append(range(start, idx))
                    start = None
            if start is not None:
                ranges.append(range(start, len(bool_array)+1)) # fuck this +1
            return ranges
        
        start = min(max(0,start),self.amt_chars)
        end = min(max(0,end),self.amt_chars)
        if end < start:
            start, end = end, start
        ranges = bool_chunks([x in self.chars for x in range(start, end)])

        if ranges:
            if max(ranges[-1])-min(ranges[0]) < 2**16:
                chars = _get_file(start,end)
                _put_cache(chars,start)
            else:
                for r in ranges:
                    chars = _get_file(min(r),max(r))
                    _put_cache(chars, min(r))
        
        # something_left = set(range(start,end)) - self.chars.keys()
        # if something_left:
        #     print(f'\n\nsomething left \t{len(something_left) = }')
        #     print(f'{ranges = }')
        #     s1 = min(something_left)
        #     s2 = max(something_left)+1
        #     chars = _get_file(s1,s2)
        #     _put_cache(chars,s1)

        return _get_cache(start, end)

    def get_int(self, start:int, end:int):
        yield from (x-48 for x in self.get(start,end))

    def get_color(self, start:int, end:int): # get from cache (raw byte - 48) / 10 lerp to 0-255 and return greyscale color
        return (pygame.Color([lerp(0,255,(char-48)/9)]*3) if char in range(48,59) else pygame.Color('red') for char in self.get(start,end))

    def get_chars(self, start:int, end:int):
        return (chr(x) for x in self.get(start,end))

    def get_chr_clr(self, start:int, end:int):
        return ((chr(char),pygame.Color([lerp(0,255,(char-48)/9)]*3)) if char in range(48,59) else (chr(char),pygame.Color('red')) for char in self.get(start,end))

class Numbal:
    """big number file graphical analyzer

    Loads a big file and shows the digis in colorful ways in the look for patterns

    Args:
        file_path (str): the location of the file
        window (pygame.Surface): a surface to draw to
    """
    def __init__(self, file_path:str, window:pygame.Surface):
        self.file_interface = Numbir(file_path)
        self.file_path = file_path
        self.window = window
        self.amt_chars = os.path.getsize(self.file_path)
        self.pos = 0
        self.width = 30
        self.side_window_hovered = False
        self.side_window_pressed = False
        self.side_window_width = 100
        self.draw_symbols = True
        self.draw()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.side_window_hovered and event.button == 1:
                self.side_window_pressed = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.side_window_pressed = False

        elif event.type == pygame.MOUSEWHEEL:
            self.pos = min(max(0,self.pos - event.y),self.amt_chars//self.amt_rows)
            self.draw()

        elif event.type == pygame.MOUSEMOTION:
            if event.pos[0] > self.window.get_width() - 100:
                self.side_window_hovered = True
                if self.side_window_pressed:
                    # self.pos = int(event.pos[1] / self.window.get_height() * self.amt_chars / self.width)
                    # self.pos = min(max(0, self.pos), self.amt_chars // int(self.width))
                    self.pos = int(event.pos[1] / self.window.get_height() * (self.amt_chars//self.amt_rows))
                    self.pos = min(max(0, self.pos), self.amt_chars // int(self.amt_rows))
                    self.draw()
            else:
                self.side_window_hovered = False
                self.side_window_pressed = False

        elif event.type == pygame.VIDEORESIZE:
            self.draw()

        elif event.type == pygame.TEXTINPUT:
            if event.text == "+":
                self.width = min(max(1, self.width-1), self.window.get_width())
                self.pos = min(self.amt_chars//ceil(self.window.get_width() / self.width) - int(self.window.get_height() / self.width), self.pos)
                # self.width = min(max(1, self.width-1), self.amt_chars//self.width)
                self.draw()
            elif event.text == "-":
                self.width = min(max(1, self.width+1), self.window.get_width())
                # self.width = max(1, min(self.width+1, self.amt_chars//self.amt_rows))
                self.draw()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.draw_symbols = not self.draw_symbols
                self.draw()
                
    @ntimer.timer
    def draw3(self):
        box_size = self.window.get_width() / self.width
        amt_columns = int(self.window.get_height() / box_size) + 1
        int(self.window.get_height() / box_size) + 1
        font = pygame.font.Font("AgaveNerdFontMono-Bold.ttf", int(box_size))
        self.window.fill('grey10')
        file_start = int(self.pos * self.width)
        file_end = int(file_start + amt_columns * self.width)

        for index, (char, bgcolor) in enumerate(self.file_interface.get_chr_clr(file_start,file_end)):
            y,x = [p*box_size for p in divmod(index, self.width)]
            pygame.draw.rect(self.window, bgcolor, ((x,y),[ceil(box_size)]*2))
            if self.draw_symbols:
                txt = font.render(char, True, 'white', bgcolor)
                self.window.blit(txt, (x,y))

        # side window
        side_window_width = self.side_window_width+5 if self.side_window_hovered else self.side_window_width
        side_window = pygame.Surface((side_window_width, self.window.get_height()),pygame.SRCALPHA)
        side_window_bg = pygame.Color(0, 0, 0, 100) if self.side_window_hovered else pygame.Color(0, 0, 0, 50)
        side_window_pos_top = file_start / self.amt_chars * self.window.get_height()
        side_window_pos_bottom = file_end / self.amt_chars * self.window.get_height()
        side_window_height = max(1,side_window_pos_bottom - side_window_pos_top)
        side_window.fill(side_window_bg)
        pygame.draw.rect(side_window, pygame.Color(200, 0, 0, 100), (0, side_window_pos_top, side_window_width, side_window_height))
        self.window.blit(side_window, (self.window.get_width() - side_window_width, 0))

    @ntimer.timer
    def draw2(self):
        amt_rows = ceil(self.window.get_width() / self.width)
        amt_colums = ceil(self.window.get_height() / self.width)
        # print(amt_colums, amt_rows)
        start = int(self.pos * amt_rows)
        end = start + amt_colums * amt_rows
        # self.window.fill()
        surf = pygame.PixelArray(self.window)
        
        surf[:,:] = 0x101010
        for index, color in enumerate(self.file_interface.get_color(start,end)):
            y,x = [p*self.width for p in divmod(index, int(amt_rows))]
            surf[x:x+self.width, y:y+self.width] = color
            # surf[y:y+self.width, x:x+self.width] = color

    @ntimer.timer
    def draw(self):
        amt_rows = self.amt_rows = ceil(self.window.get_width() / self.width)
        amt_colums = ceil(self.window.get_height() / self.width)
        start = self.pos*amt_rows
        end = start + amt_colums * amt_rows
        colors1d = np.array(list(self.file_interface.get_int(start,end))) * 28.334
        colors1d = np.pad(colors1d, (0,max(0,amt_colums*amt_rows-colors1d.shape[0])))
        colors2d = colors1d.reshape((amt_colums,amt_rows)).T
        colors_array = np.stack((colors2d,) * 3, axis=-1)
        surface = pygame.surfarray.make_surface(colors_array)
        surface_sclaled = pygame.transform.scale(surface, self.window.get_size())
        self.window.blit(surface_sclaled,(0,0))

def main():
    pygame.font.init()
    winsize = (800, 600)
    window = pygame.display.set_mode(winsize, pygame.SRCALPHA|pygame.RESIZABLE)
    pygame.display.set_caption("numbal")
    n = Numbal(r"\\10.0.0.3\raid\other\bignum\e\e - Dec - exp(1).txt", window)
    # n = Numbal(r"test.txt", window)
    clock = pygame.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            n.handle_input(event)

        pygame.display.flip()
        clock.tick(60)
        # print(clock.get_fps(),end="\r")

if __name__ == '__main__':
    main()