from enum import Enum
from typing import Tuple, Union, Optional, NamedTuple
from .utils import Point3f

Rect = Tuple[int, int, int, int]
Color3i = Tuple[int, int, int]
# Color4i = Tuple[int, int, int, int]
Color3f = Tuple[float, float, float]


class Color4f(NamedTuple):
    r: float
    g: float
    b: float
    a: float

    def __add__(self, other: 'Color4f') -> 'Color4f':
        if isinstance(other, Color4f):
            return Color4f(self.r + other.r, self.g + other.g, self.b + other.b, 1.0)
        raise TypeError()

    def __mul__(self, other: float):
        if isinstance(other, float):
            return Color4f(self.r * other, self.g * other, self.b * other, 1.0)
        if isinstance(other, Color4f):
            return Color4f(self.r * other.r, self.g * other.g, self.b * other.b, 1.0)
        raise TypeError(f"Can't multiply Color4f by {type(other)}")

    def __rmul__(self, other: float):
        return self * other

    def trim(self) -> 'Color4f':
        return Color4f(
            0.0 if self.r < 0.0 else (1.0 if self.r > 1.0 else self.r),
            0.0 if self.g < 0.0 else (1.0 if self.g > 1.0 else self.g),
            0.0 if self.b < 0.0 else (1.0 if self.b > 1.0 else self.b),
            0.0 if self.a < 0.0 else (1.0 if self.a > 1.0 else self.a),
        )


class Interpolation(Enum):
    NONE = 0
    LINEAR = 1


class PNMLoader:
    @classmethod
    def from_pnm(cls, path: str, *,
                 crop_to: Optional[Rect] = None,
                 transparency: Optional[Color3i] = None) -> 'Image':
        """
        Read texture from P3 (RGB ascii) PNM format.
        
        @param path:
        @param crop_to:
        @param transparency:
        """
        with open(path) as file:
            lines = [line.strip() for line in file]
            lines = [line for line in lines if not line.startswith('#')]  # remove comments

            assert lines[0] == 'P3'        
            width, height = map(int, lines[1].split())
            assert lines[2] == '255'

            # Read colors info
            values = []
            for pos in range(3, len(lines), 3):
                r, g, b = map(int, lines[pos: pos+3])
                
                color = (r/255, g/255, b/255, 0.0 if (r, g, b) == transparency else 1.0)
                values.append(color)
            
            assert len(values) == width * height

        # Build Image instance
        texture = Image(width=width, height=height)
        for y in range(height):
            for x in range(width):
                texture[x, y] = values[y * width + x]

        if crop_to:
            return texture.crop(crop_to)

        return texture


class Image(PNMLoader):
    @property
    def width(self):
        return self._width


    @property
    def height(self):
        return self._height

    @property
    def size(self):
        return (self._width, self._height)


    def __init__(self, *, width: int, height: int):
        """Create empty white texture of given size."""
        assert (width > 0) and (height > 0)

        self._width = width
        self._height = height
        self._data = [(1.0, 1.0, 1.0, 1.0)] * (width*height)


    def __setitem__(self, position: Tuple[int, int], value: Union[Color3f, Color4f]):
        assert 3<= len(value) <= 4, f"{value}" # RGB or RGBA

        x, y = position
        assert (0 <= x < self._width) and (0 <= y < self._height)

        if len(value) == 3:  # RGB color
            value = value + (255, )

        self._data[y*self._width + x] = value


    def __getitem__(self, position: Tuple[int, int]) -> Color4f:
        x, y = position
        assert (0 <= x < self._width) and (0 <= y < self._height)

        return Color4f(*self._data[y * self._width + x])

    def crop(self, crop_to: Rect) -> 'Image':
        """
        Crop texture to given rectangle.
        
        @param crop_to_: (x0, y0, x1, y1)
        """
        x0, y0, x1, y1 = crop_to
        assert (0 <= x0 <= x1 < self._width) and (0 <= y0 <= y1 < self._height)

        texture = Image(width=(x1-x0+1), height=(y1-y0+1))
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                texture[x - x0, y - y0] = self[x,y]

        return texture

    def interpolate(self, point: Point3f, *, interpolation: Interpolation = Interpolation.NONE) -> Color4f:
        # print(point)
        x, y = round((self.width-1) * point.x), round((self.height-1) * point.y)
        return self[x, y]
        # raise NotImplementedError()


if __name__ == '__main__':
    torch = Image.from_pnm('gfx/torch.pnm')
    print(torch.width, torch.height)
    print(torch[12,12])
    torch = Image.from_pnm('gfx/torch.pnm', transparency=(0, 255, 255))
    print(torch[12,12])
    torch2 = torch.crop((0, 0, 4, 4))
    print(torch2.width, torch2.height)