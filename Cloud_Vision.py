# 이미지/동영상을 base64로 인코딩한 stream 값을 만들기 위함
import io
import json


# 전역변수를 encapsulation
class FeatureType:
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def detect_img_text(path):
    """
    수령한 이미지를 vision api를 사용해 텍스트로 변환한 후 해당 텍스트 반환
    :param path: 원본 이미지 (경로+파일명)
    :return: String
    """
    """Detects text in the file."""
    from google.cloud import vision
    from google.protobuf.json_format import MessageToDict

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    # response = client.text_detection(image=image)
    # texts = response.text_annotations

    response = client.document_text_detection(image=image)
    json_obj = MessageToDict(response)

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        #     # return_text = texts[0].description
        #     # return return_text
        #     return texts
        return json_obj


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
    전달받은 dictionary 중 각 단위에 맞게 좌표 배열만 추출해서 전달
    :param document: OCR 객체
    :param feature: 어떤 단위를 칠할 건지 (page, block, paragraph, word, symbol)
    :return: bound array(x1, y1....x4,y4)
    """
    from google.cloud import vision

    # 리턴할 배열
    bounds = []
    paragraphs = []
    lines = []
    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

    for page in document["fullTextAnnotation"]["pages"]:
        for block in page["blocks"]:
            for paragraph in block["paragraphs"]:
                para = ""
                line = ""
                for word in paragraph["words"]:
                    for symbol in word["symbols"]:
                        if feature == FeatureType.SYMBOL:
                            bounds.append(symbol["boundingBox"])
                        line += symbol["text"]
                        try:
                            symbol["property"]["detectedBreak"]
                        except:
                            # print("no key! - ", line + symbol["text"])
                            continue

                        # 각 character들을 합치되, \n, space도 포함할 것
                        if symbol["property"]["detectedBreak"]["type"] == breaks.SPACE:
                            line += ' '
                        if symbol["property"]["detectedBreak"]["type"] == breaks.EOL_SURE_SPACE:
                            line += ' '
                            lines.append(line)
                        if symbol["property"]["detectedBreak"]["type"] == breaks.LINE_BREAK:
                            lines.append(line)
                            para += line
                            line = ''

                    if feature == FeatureType.WORD:
                        bounds.append(word["boundingBox"])
                paragraphs.append(para)
                if feature == FeatureType.PARA:
                    bounds.append(paragraph["boundingBox"])

            if feature == FeatureType.BLOCK:
                bounds.append(block["boundingBox"])

    return [paragraphs, bounds]
