# 이미지/동영상을 base64로 인코딩한 stream 값을 만들기 위함
import io


def detect_img_text(path):
    """
    수령한 이미지를 vision api를 사용해 텍스트로 변환한 후 해당 텍스트 반환
    :param path: 원본 이미지 (경로+파일명)
    :return: String
    """
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        return_text = texts[0].description
        return return_text
