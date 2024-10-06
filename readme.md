# Minimal Image Duplication Detector Module

## Overview

This Python module implements image duplication detection as presented in the paper "NFT Duplications detection using 
Image hash functions". The module implements the One-Minimal detector, using a **BK-tree** to store images.

The module provides efficient image addition and duplication checking, leveraging basic Python parallel-running features to enhance performance.

## Features

- **One-Minimal Duplication Detector**: A simple and fast duplication detection function, based on image-hashing.
- **BK-tree Based**: The module utilizes BK-trees for efficient similarity search.
- **Parallel Execution**: Parallel processing is implemented to optimize the search and detection process.

## Functionality

### `add_image_to_dataset(image, name=None)`

This function allows users to add an image to the dataset for future duplication checks. It updates the BK-tree structure with the new image.

#### Parameters:
- `image`: The image to be added.
- `name`: The image path or name (optional).

### `check_image_for_duplications(image)`

This function checks if the image is a duplication of an existing image in the DB.

#### Parameters:
- `image`: The image to be checked.

#### Example:
```python
from PIL import Image
from minimal_distance_detector import MinimalDistanceDetector

image_1_path = "PATH_TO_IMAGE_1"
image_2_path = "PATH_TO_IMAGE_2"

detector = MinimalDistanceDetector()

# Add an image to dataset
image_1 = Image.open(image_1_path, image_1_path)
detector.add_image_to_dataset(image_1)

image_2 = Image.open(image_2_path)

# Test image for duplications
found_duplication = detector.check_image_for_duplications(image_2)
if detector.check_image_for_duplications(image_2):
    print(f"{image_2} is a duplication of an existing image in the dataset.")
else:
    print(f"{image_2} is not a duplication.")
```
