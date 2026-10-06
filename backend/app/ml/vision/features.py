"""Small, interpretable image features shared by inference and training."""

from math import sqrt

from app.ml.vision.preprocessing import load_and_resize

LEGACY_FEATURE_NAMES = (
    "brightness_mean",
    "brightness_std",
    "dark_pixel_ratio",
    "brown_pixel_ratio",
    "green_pixel_ratio",
    "red_mean",
    "green_mean",
    "blue_mean",
)
FEATURE_NAMES = (
    *LEGACY_FEATURE_NAMES,
    *(f"brightness_histogram_{index}" for index in range(8)),
    "saturation_mean",
    "saturation_std",
    *(f"quadrant_{index}_brightness_mean" for index in range(4)),
    *(f"quadrant_{index}_brown_ratio" for index in range(4)),
)


def extract_image_features(
    image_path: str, feature_names: tuple[str, ...] | None = None
) -> tuple[list[float], dict[str, float]]:
    """Return v2 features by default, or the legacy vector for old artifacts."""
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

        legacy_vector = [
            brightness / 255,
            brightness_std / 255,
            dark_ratio,
            brown_ratio,
            green_ratio,
            channel_means[0] / 255,
            channel_means[1] / 255,
            channel_means[2] / 255,
        ]
        histogram = [0] * 8
        saturation_values = []
        quadrant_counts = [0] * 4
        quadrant_brightness = [0.0] * 4
        quadrant_brown = [0] * 4
        width, height = image.size
        half_width = max(width // 2, 1)
        half_height = max(height // 2, 1)
        for index, (red, green, blue) in enumerate(pixels):
            value = brightness_values[index]
            histogram[min(int(value // 32), 7)] += 1
            maximum, minimum = max(red, green, blue), min(red, green, blue)
            saturation_values.append((maximum - minimum) / max(maximum, 1))
            quadrant = (index // width // half_height) * 2 + (index % width // half_width)
            quadrant = min(quadrant, 3)
            quadrant_counts[quadrant] += 1
            quadrant_brightness[quadrant] += value
            quadrant_brown[quadrant] += (
                red > green * 1.12 and green > blue * 1.08 and 35 < value < 180
            )
        saturation_mean = sum(saturation_values) / count
        saturation_std = sqrt(
            sum((value - saturation_mean) ** 2 for value in saturation_values) / count
        )
        expanded_vector = [
            *legacy_vector,
            *(value / count for value in histogram),
            saturation_mean,
            saturation_std,
            *(total / (max(size, 1) * 255) for total, size in zip(quadrant_brightness, quadrant_counts, strict=True)),
            *(brown / max(size, 1) for brown, size in zip(quadrant_brown, quadrant_counts, strict=True)),
        ]
        vector = legacy_vector if feature_names == LEGACY_FEATURE_NAMES else expanded_vector
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
