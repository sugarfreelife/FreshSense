"""Small, interpretable image features shared by inference and training."""

from math import sqrt

from app.ml.vision.preprocessing import load_and_resize

FEATURE_NAMES = (
    "brightness_mean",
    "brightness_std",
    "dark_pixel_ratio",
    "brown_pixel_ratio",
    "green_pixel_ratio",
    "red_mean",
    "green_mean",
    "blue_mean",
)


def extract_image_features(image_path: str) -> tuple[list[float], dict[str, float]]:
    image = load_and_resize(image_path, size=(128, 128))
    try:
        pixels = image.get_flattened_data()
        count = max(len(pixels), 1)
        channel_sums = [sum(pixel[channel] for pixel in pixels) for channel in range(3)]
        channel_means = [value / count for value in channel_sums]
        brightness_values = [(red + green + blue) / 3 for red, green, blue in pixels]
        brightness = sum(brightness_values) / count
        brightness_std = sqrt(sum((value - brightness) ** 2 for value in brightness_values) / count)
        dark_ratio = sum(value < 60 for value in brightness_values) / count
        brown_ratio = sum(
            red > green * 1.12 and green > blue * 1.08 and 35 < (red + green + blue) / 3 < 180
            for red, green, blue in pixels
        ) / count
        green_ratio = sum(green > red * 1.12 and green > blue * 1.08 for red, green, blue in pixels) / count

        vector = [
            brightness / 255,
            brightness_std / 255,
            dark_ratio,
            brown_ratio,
            green_ratio,
            channel_means[0] / 255,
            channel_means[1] / 255,
            channel_means[2] / 255,
        ]
        evidence = {
            "mean_brightness": round(brightness, 2),
            "brightness_variation": round(brightness_std, 2),
            "dark_pixel_ratio": round(dark_ratio, 4),
            "brown_pixel_ratio": round(brown_ratio, 4),
            "green_pixel_ratio": round(green_ratio, 4),
        }
        return vector, evidence
    finally:
        image.close()
