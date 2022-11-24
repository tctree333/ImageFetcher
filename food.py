import os
import json
from google.cloud import vision

credentials = os.getenv("VISION_API_CREDENTIALS", "")
info = json.loads(credentials)
client = vision.ImageAnnotatorClient.from_service_account_info(info)


class FoodException(Exception):
    def __init__(self, message):
        super().__init__(message)


def food(data: bytes = None, url: str = None) -> tuple:
    """Detects if an image contains food.

    Returns a tuple with the first item a boolean (whether it has food)
    and the second item a dict mapping detected labels to scores.

    Based on the example label classification code on Google Cloud Docs.
    """

    image = vision.Image()
    if data is not None:
        image = vision.Image(content=data)
    elif url is not None:
        image.source.image_uri = url
    else:
        raise FoodException("Either data or url need to be provided!")

    response = client.label_detection(image=image, max_results=10)
    labels = {
        label.description.lower(): label.score for label in response.label_annotations
    }

    if response.error.message:
        raise FoodException(
            "{}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors".format(
                response.error.message
            )
        )

    return (labels.get("food", 0) >= 0.70, labels)
