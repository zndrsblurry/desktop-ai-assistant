"""
Computer Vision Utilities

Provides functions for image processing tasks relevant to screen interaction,
such as template matching (finding an image within another) and OCR
(extracting text from images).
"""

import logging
from typing import Optional, Tuple, List, Any, Dict
import numpy as np

# OpenCV for image processing and template matching
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    logging.warning(
        "OpenCV (cv2) not found. Vision features like template matching will be unavailable. Install with: pip install opencv-python"
    )
    cv2 = None
    CV2_AVAILABLE = False

# OCR library (e.g., pytesseract + Tesseract-OCR engine)
try:
    import pytesseract

    # You might need to configure the path to the Tesseract executable:
    # pytesseract.pytesseract.tesseract_cmd = r'/path/to/your/tesseract' # Example
    TESSERACT_AVAILABLE = True
except ImportError:
    logging.warning(
        "pytesseract not found or Tesseract-OCR engine not installed/configured. OCR features will be unavailable. Install pytesseract: pip install pytesseract. Install Tesseract engine separately."
    )
    pytesseract = None
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


def find_template_on_screen(
    template_image_path: str,
    screen_image: Optional[np.ndarray] = None,
    threshold: float = 0.8,
    method: int = cv2.TM_CCOEFF_NORMED if CV2_AVAILABLE else 0,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Finds a smaller template image within a larger screen image.

    Args:
        template_image_path: Path to the template image file to search for.
        screen_image: The screen capture (as a NumPy array, BGRA or BGR format).
                      If None, captures the primary screen automatically (requires screen.py utils).
        threshold: Matching threshold (0.0 to 1.0). Higher means stricter match.
        method: OpenCV template matching method (e.g., cv2.TM_CCOEFF_NORMED).

    Returns:
        A tuple (x, y, width, height) of the found template's bounding box
        relative to the screen_image, or None if not found or libraries unavailable.
    """
    if not CV2_AVAILABLE:
        logger.error("OpenCV is required for template matching.")
        return None

    try:
        template = cv2.imread(
            template_image_path, cv2.IMREAD_UNCHANGED
        )  # Load with alpha if present
        if template is None:
            logger.error(f"Could not load template image: {template_image_path}")
            return None

        if screen_image is None:
            # Capture primary screen if none provided
            from .screen import (
                capture_screen_mss,
            )  # Local import to avoid circular dependency if needed

            screen_image = capture_screen_mss(monitor_id=1)  # Capture primary monitor
            if screen_image is None:
                logger.error("Failed to capture screen for template matching.")
                return None

        # Ensure screen image is in BGR format (OpenCV standard)
        if screen_image.shape[2] == 4:  # BGRA
            screen_bgr = cv2.cvtColor(screen_image, cv2.COLOR_BGRA2BGR)
        elif screen_image.shape[2] == 3:  # BGR
            screen_bgr = screen_image
        else:
            logger.error("Unsupported screen image format for template matching.")
            return None

        # Handle template alpha channel if present (for masked matching)
        mask = None
        if template.shape[2] == 4:
            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
            mask = template[:, :, 3]  # Use alpha channel as mask
            threshold = threshold * 0.9  # Adjust threshold for masked matching
        else:
            template_bgr = template

        # Perform template matching
        logger.debug(
            f"Performing template matching with method {method} and threshold {threshold:.2f}"
        )
        result = cv2.matchTemplate(screen_bgr, template_bgr, method, mask=mask)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        logger.debug(
            f"Template matching result: Max value = {max_val:.4f} at location {max_loc}"
        )

        # Get the best match location based on the method
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
            match_val = min_val  # Lower is better
            is_match = match_val <= (1.0 - threshold)  # Adjust threshold interpretation
        else:
            top_left = max_loc
            match_val = max_val  # Higher is better
            is_match = match_val >= threshold

        if is_match:
            h, w = template_bgr.shape[:2]
            # bottom_right = (top_left[0] + w, top_left[1] + h)
            logger.info(
                f"Template found at ({top_left[0]}, {top_left[1]}) with confidence {match_val:.4f}"
            )
            # Return (x, y, width, height)
            return (top_left[0], top_left[1], w, h)
        else:
            logger.debug(
                f"Template not found above threshold {threshold:.2f} (Best match: {match_val:.4f})"
            )
            return None

    except Exception as e:
        logger.exception(f"Error during template matching: {e}")
        return None


def extract_text_from_image(
    image: np.ndarray,
    lang: str = "eng",
    config: str = "",  # Additional Tesseract config options (e.g., '--psm 6')
) -> Optional[str]:
    """
    Extracts text from an image using Tesseract OCR via pytesseract.

    Args:
        image: The image (as a NumPy array, BGR or Grayscale format).
        lang: The language code for OCR (e.g., 'eng', 'fra'). Requires language pack installed.
        config: Additional Tesseract configuration flags.

    Returns:
        The extracted text as a string, or None if OCR fails or library unavailable.
    """
    if not TESSERACT_AVAILABLE:
        logger.error("pytesseract/Tesseract-OCR is required for OCR.")
        return None
    if not CV2_AVAILABLE:
        logger.error("OpenCV is required for image preprocessing for OCR.")
        return None

    try:
        # Ensure image is suitable for OCR (e.g., grayscale often works well)
        if len(image.shape) == 3:  # Color image (assume BGR)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Optional: Apply thresholding or other preprocessing
            # _, processed_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_image = gray_image  # Use grayscale directly for now
        elif len(image.shape) == 2:  # Grayscale
            processed_image = image
        else:
            logger.error("Unsupported image format for OCR.")
            return None

        logger.debug(f"Performing OCR with language '{lang}' and config '{config}'")
        # Perform OCR
        text = pytesseract.image_to_string(processed_image, lang=lang, config=config)

        logger.info(f"OCR extracted {len(text)} characters.")
        return text.strip()

    except pytesseract.TesseractNotFoundError:
        logger.error(
            "Tesseract executable not found or not in PATH. Configure pytesseract.pytesseract.tesseract_cmd."
        )
        # Disable further attempts?
        global TESSERACT_AVAILABLE
        TESSERACT_AVAILABLE = False
        return None
    except Exception as e:
        logger.exception(f"Error during OCR text extraction: {e}")
        return None


def get_ocr_data(
    image: np.ndarray,
    lang: str = "eng",
    config: str = "--psm 6",  # Assume sparse text layout
) -> Optional[List[Dict[str, Any]]]:
    """
    Extracts detailed OCR data (text, bounding boxes, confidence) from an image.

    Args:
        image: The image (as a NumPy array, BGR or Grayscale format).
        lang: The language code for OCR.
        config: Additional Tesseract configuration flags (e.g., PSM modes).

    Returns:
        A list of dictionaries, each representing a detected text block with
        keys like 'level', 'page_num', 'block_num', 'par_num', 'line_num',
        'word_num', 'left', 'top', 'width', 'height', 'conf', 'text'.
        Returns None on failure.
    """
    if not TESSERACT_AVAILABLE:
        logger.error("pytesseract/Tesseract-OCR is required for OCR data extraction.")
        return None
    if not CV2_AVAILABLE:
        logger.error("OpenCV is required for image preprocessing for OCR.")
        return None

    try:
        # Preprocess image (similar to extract_text_from_image)
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            processed_image = gray_image
        elif len(image.shape) == 2:
            processed_image = image
        else:
            logger.error("Unsupported image format for OCR data.")
            return None

        logger.debug(
            f"Performing detailed OCR with language '{lang}' and config '{config}'"
        )
        # Perform OCR using image_to_data
        data_dict = pytesseract.image_to_data(
            processed_image,
            lang=lang,
            config=config,
            output_type=pytesseract.Output.DICT,  # Get results as dictionary
        )

        # Process the dictionary into a list of detected words/blocks
        ocr_results = []
        num_items = len(data_dict["level"])
        for i in range(num_items):
            # Filter out items with negative confidence (often non-text blocks)
            # and empty text strings (often spaces between words)
            conf = int(data_dict["conf"][i])
            text = data_dict["text"][i].strip()
            if (
                conf > 0 and text
            ):  # Confidence threshold can be adjusted (e.g., conf > 50)
                ocr_results.append(
                    {
                        "level": data_dict["level"][i],
                        "page_num": data_dict["page_num"][i],
                        "block_num": data_dict["block_num"][i],
                        "par_num": data_dict["par_num"][i],
                        "line_num": data_dict["line_num"][i],
                        "word_num": data_dict["word_num"][i],
                        "left": data_dict["left"][i],
                        "top": data_dict["top"][i],
                        "width": data_dict["width"][i],
                        "height": data_dict["height"][i],
                        "conf": conf,
                        "text": text,
                    }
                )

        logger.info(f"Detailed OCR found {len(ocr_results)} text items.")
        return ocr_results

    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract executable not found or not in PATH.")
        global TESSERACT_AVAILABLE
        TESSERACT_AVAILABLE = False
        return None
    except Exception as e:
        logger.exception(f"Error during detailed OCR data extraction: {e}")
        return None
