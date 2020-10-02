# 이미지/동영상을 base64로 인코딩한 stream 값을 만들기 위함
import io
from enum import Enum


# 전역변수를 encapsulation
class FeatureType(Enum):
    PAGE   = 1
    BLOCK  = 2
    PARA   = 3
    WORD   = 4
    SYMBOL = 5


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


def detect_img_text_n_coord(path):
    """
    수령한 이미지를 vision api를 사용해 텍스트로 변환한 후 해당 텍스트 반환
    :param path: 원본 이미지 (경로+파일명)
    :return: list[text:coordinates]
    """
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    document = response.full_text_annotations

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        return document


# symbol = recognized object of character
def assemble_word(word):
    assembled_word = ""
    for symbol in word.symbols:
        assembled_word += symbol.text

    return assembled_word


def find_word_location(document, word_to_find, is_regex):
    """
    OCR Response 객체에서 지정된 단어 탐색, regex 옵션이 true면 regex로 탐색
    만약 OCR Response를 물고 있는 채로 작업할거면 이 함수를 살려서 쓸 것
    :param document:
    :param word_to_find:
    :param is_regex:
    :return:
    """
    import re
    p = None

    if is_regex:
        p = re.compile(word_to_find)

    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    assembled_word = assemble_word(word)
                    if p is not None:
                        match_obj = p.search(word)
                        if match_obj is not None:
                            return word.bounding_box
                            # return match_obj.group()
                    else:
                        if assembled_word == word_to_find:
                            return word.bounding_box


def get_document_bounds(document, feature):
    """
    전달받은 response 객체값에서 텍스트/좌표를 dataframe으로
    :param document: OCR 객체
    :param feature: 어떤 코드에 매핑되는 지는 상단의 FeatureType class 참조
    :return: dataframe(text, x1, y1, x)
    """
    # 리턴 객체를 담기 위한 임시 import
    import pandas as pd

    # 각 텍스트와 좌표를 담을 녀석
    text = []
    confidence = []
    coord_x1 = []
    coord_y1 = []
    coord_x2 = []
    coord_y2 = []
    coord_x3 = []
    coord_y3 = []
    coord_x4 = []
    coord_y4 = []

    # 임시로 좌표 리스트들을 담아둘 리스트
    bounds = []

    for page in document.pages:
        # 페이지별 bound 필요 시
        if feature == FeatureType.PAGE:
            text.append(page.text)
            confidence.append(page.confidence)
            bounds.append(page.bounding_box)
        else:
            # 블록별 bound 필요 시
            for block in page.blocks:
                if feature == FeatureType.BLOCK:
                    text.append(block.text)
                    confidence.append(block.confidence)
                    bounds.append(block.bounding_box)
                else:
                    # 단락별 bound 필요 시
                    for paragraph in block.paragraphs:
                        if feature == FeatureType.PARA:
                            text.append(paragraph.text)
                            confidence.append(paragraph.confidence)
                            bounds.append(paragraph.bounding_box)
                        else:
                            # 단어별 bound 필요 시
                            for word in paragraph.words:
                                if feature == FeatureType.WORD:
                                    text.append(word.text)
                                    confidence.append(word.confidence)
                                    bounds.append(word.bounding_box)
                                else:
                                    # 문자별 bound 필요 시
                                    for symbol in word.symbols:
                                        if feature == FeatureType.SYMBOL:
                                            text.append(symbol.text)
                                            confidence.append(symbol.confidence)
                                            bounds.append(symbol.bounding_box)

    # bounds 객체를 나눠서 저장
    for bound in bounds:
        coord_x1.append(bound.vertices[0].x)
        coord_y1.append(bound.vertices[0].y)
        coord_x2.append(bound.vertices[1].x)
        coord_y2.append(bound.vertices[1].y)
        coord_x3.append(bound.vertices[2].x)
        coord_y3.append(bound.vertices[2].y)
        coord_x4.append(bound.vertices[3].x)
        coord_y4.append(bound.vertices[3].y)

    ret_df = pd.DataFrame({
        "text": text,
        "confidence": confidence,
        "coord_x1": coord_x1,
        "coord_y1": coord_y1,
        "coord_x2": coord_x2,
        "coord_y2": coord_y2,
        "coord_x3": coord_x3,
        "coord_y3": coord_y3,
        "coord_x4": coord_x4,
        "coord_y4": coord_y4
    })

    return ret_df
