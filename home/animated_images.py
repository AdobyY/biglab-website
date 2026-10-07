"""Keep GIF frames through Wagtail's normal crop and resize pipeline."""

from PIL import Image as PILImage, ImageSequence
from willow.image import GIFImageFile, Image
from willow.plugins.pillow import PillowImage
from willow.registry import registry


class AnimatedPillowImage(Image):
    def __init__(self, source, operations=(), poster=None):
        self.source = source
        self.operations = operations
        self.loop = source.info.get('loop')
        self.image = poster if poster is not None else source.convert('RGBA')

    @classmethod
    @Image.converter_from(GIFImageFile, cost=0)
    def open(cls, image_file):
        image_file.f.seek(0)
        return cls(PILImage.open(image_file.f))

    def transformed(self, operation):
        # Apply transforms while decoding instead of expanding every original frame into RAM.
        return type(self)(self.source, self.operations + (operation,), operation(self.image))

    @Image.operation
    def auto_orient(self):
        return self

    @Image.operation
    def get_size(self):
        return self.image.size

    @Image.operation
    def get_frame_count(self):
        return self.source.n_frames

    @Image.operation
    def has_animation(self):
        return self.source.n_frames > 1

    @Image.operation
    def has_alpha(self):
        return 'transparency' in self.source.info

    @Image.operation
    def crop(self, rect):
        return self.transformed(lambda frame: frame.crop(tuple(rect)))

    @Image.operation
    def resize(self, size):
        return self.transformed(lambda frame: frame.resize(size, PILImage.Resampling.LANCZOS))

    @Image.operation
    def save_as_gif(self, output, apply_optimizers=True):
        # A reserved palette entry keeps transparent backgrounds transparent.
        frames, durations = [], []
        self.source.seek(0)
        for source_frame in ImageSequence.Iterator(self.source):
            durations.append(source_frame.info.get('duration', 100))
            frame = source_frame.convert('RGBA')
            for operation in self.operations:
                frame = operation(frame)
            palette = frame.convert('RGB').quantize(colors=255)
            mask = frame.getchannel('A').point(lambda alpha: 255 if alpha < 128 else 0)
            palette.paste(255, mask=mask)
            palette.info['transparency'] = 255
            frames.append(palette)
        options = dict(save_all=True, append_images=frames[1:], duration=durations,
                       disposal=2, transparency=255, optimize=False)
        if self.loop is not None:
            options['loop'] = self.loop
        frames[0].save(output, format='GIF', **options)
        return GIFImageFile(output)

    @Image.converter_to(PillowImage, cost=200)
    def still_frame(self):
        # Explicit PNG/JPEG output is used for posters and intentionally static contexts.
        return PillowImage(self.image.copy())


def register():
    registry.register_image_class(AnimatedPillowImage)
