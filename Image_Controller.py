import os
import shutil
# pdf 를 이미지로 변환하기 위한 패키지
from pdf2image import convert_from_path
# 이미지 슬라이싱을 위한 패키지들
import numpy as np
# 이미지 회전 및 리사이징 시 사용
import cv2
# 이미지 회전을 위한 패키지들
from scipy import ndimage
import statistics
import math
# IO 관련 유틸 함수 모음
import Util
# 에러 발생 시 처리용
import traceback


"""
Interface Function
move_img <- pdf_to_image
cleansed_img <- resize_img, rotate_img, crop_img
"""


def move_img(original_path, target_path):
    """
    original_path 경로에 있는 pdf 파일/이미지 파일들을 target_path에 온전히 이미지 파일로만 적재
    :param original_path: Invoice 원본이 적재된 경로
    :param target_path: pdf를 이미지로 변환하여 적재할 경로 (원본 이미지의 경우 그대로 복사하여 이 경로로 이동)
    :return: None
    """
    for filename in os.listdir(original_path):
        # 경로인지 파일인지 탐색 및 경로면 넘어가기
        if os.path.isdir(filename):
            print(filename + "=경로입니다.")
            continue
        # 만일 이미 format 된 거면 넘어가기
        if Util.is_duplicated(filename, target_path):
            print("Already formatted : ", filename)
            continue

        # 파일 형식이 pdf면 pdf를 이미지로 변환
        if filename.lower().endswith('.pdf'):
            print("PDF 이미지화: ", filename)
            pdf_to_img(original_path, filename, target_path)
        # 이미지 형식이면 복사
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            shutil.copy(original_path + filename, target_path + filename)
        # 지정된 형식이 아닐 경우 넘어가기
        else:
            print(filename + ': 지정되지 않은 형식. .pdf, .png, .jpg, .jpeg 가 아니면 안됩니다.')


def pdf_to_img(path, filename, save_dir):
    """
    전달 받은 pdf 파일 내 장수 상관 없이 모두 이미지 파일로 변경
    :param path: pdf 파일 경로
    :param filename: pdf 파일명
    :param save_dir: 이미지 변환 후 저장할 경로
    :return: None
    """
    # 대상 pdf에서 확장자명 제외하고 이름만 추출
    base_filename = os.path.splitext(os.path.basename(filename))[0]
    try:
        # pdf 파일 내 각 장을 리스트로 변환
        pages = convert_from_path(path + filename)
        # 만약 한장이라면
        if len(pages) == 1:
            # 0번째 index를 가져옴 (한장이더라도 리스트로 반환하기 때문)
            pages[0].save(os.path.join(save_dir, base_filename) + '.jpg', 'JPEG')
        else:
            # 여러장이면 각 장을 [0], [1] 순으로 파일 인덱싱을 새로 하여 저장
            page_count = 1
            for page in pages:
                page.save(os.path.join(save_dir, base_filename) +
                          '(' + str(page_count) + ').jpg', 'JPEG')
                page_count += 1

    except Exception as ex:
        print("PDF 파일을 이미지로 변환하는데 실패했습니다: " + filename + " -> {}".format(ex))
        # 혹시 일부가 이미 이미지로 변환되었다면 해당 파일을 모두 지울 것
        for img in os.listdir(save_dir):
            if base_filename in img:
                os.remove(path + img)


def cleanse_img(formatted_path, cleansed_path, resize_standard, coord_dict):
    """
    format된 이미지들을 전처리 및 지정된 경로로 다른 이름 저장 (이미지 리사이즈, crop)
    :param formatted_path: 전처리 대상 파일 경로
    :param cleansed_path: 전처리 후 저장할 경로
    :param resize_standard: 리사이징 표준 너비/높이
    :param coord_dict: crop 시 사용할 좌표 리스트
    :return:
    """
    # formatted 된 경로 순회
    for img_file in os.listdir(formatted_path):
        # 경로인지 파일인지 탐색 및 경로면 넘어가기
        if os.path.isdir(img_file):
            print(img_file + "=경로입니다.")
            continue
        # 이미 정제된 파일인지 확인
        if Util.is_duplicated(img_file, cleansed_path):
            print("Already Cleansed : ", img_file)
            continue

        # cv2로 읽은 이미지 객체 만들기
        src_img = read_unicode_img(formatted_path + img_file)

        # 이미지 리사이즈
        resized = cv2.resize(src_img,
                             dsize=(resize_standard[0], resize_standard[1]),
                             interpolation=cv2.INTER_LINEAR
                             )

        # 좌표를 가졌는지 판단하는 플래그, 나중에 정규표현식 말아먹으면 대체할 것
        # cropped = crop_img(img_file, resized, coord_dict)
        cropped = None
        # 만일 crop이 성공했다면
        if cropped is not None:
            result = write_unicode_img(cleansed_path + img_file, cropped)
            print(img_file, " result = ", result)
        # 아니라면 리사이징 결과만 저장
        else:
            result = write_unicode_img(cleansed_path + img_file, resized)
            print(img_file, " result = ", result)


def rotate_img(path, filename):
    """
    cv2의 허프 변환 함수를 이용해 이미지의 회전 여부 파악 및 0.1도 이상 회전된 것을 감지 시 변환
    :param path: 검사할 파일이 속한 경로
    :param filename: 검사할 파일명
    :return: None
    """
    img_before = cv2.imread(path + filename)

    img_gray = cv2.cvtColor(img_before, cv2.COLOR_BGR2GRAY)
    img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
    lines = cv2.HoughLinesP(img_edges, 1, math.pi / 180.0, 100, minLineLength=100, maxLineGap=5)

    angles = []

    for [[x1, y1, x2, y2]] in lines:
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        angles.append(angle)

    median_angle = statistics.median(angles)
    img_rotated = ndimage.rotate(img_before, median_angle)

    print(f"filename + Angle is {median_angle:.04f}")
    # cv2.imwrite('rotated.jpg', img_rotated)


def crop_img(filename, src_img, coord_dict):
    """
    좌표 리스트 내 지정된 파일이 존재할 경우 특정 영역 추출 및 저장
    :param filename: 원번 이미지 객체의 파일명
    :param src_img: 원본 이미지 객체
    :param coord_dict: 파일들 중 일부는 특정 영역만 잘라서 저장해야 함
    :return: crop이 완료된 이미지 객체 OR None
    """
    # 좌표가 있는 경우 해당 행의 인덱스를 담기 위한 변수
    target_index = -1
    # 주어진 파일이 좌표 데이터 구조 내에 존재하는지 탐색
    for index in range(0, len(coord_dict)):
        # 만일 대상이 맞다면 플래그 true 찍고 좌표값 추출 및 break
        if coord_dict.loc[index, "PtrName"] in filename:
            target_index = index
            break

    # 좌표값이 존재하는 이미지는 정제 후 다른이름 저장
    if target_index != -1:
        img_array = np.array(src_img)
        # pixel 배열을 슬라이스하여 이미지 자르기
        cropped_img = src_img[
                      coord_dict.loc[target_index, "Y1"]:coord_dict.loc[target_index, "Y2"] + 1,
                      coord_dict.loc[target_index, "X1"]:coord_dict.loc[target_index, "X2"] + 1
                      ]
        return cropped_img
    # 만일 없다면 그냥 None 리턴
    else:
        return None


def read_unicode_img(uni_filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
    """
    cv2의 imread 함수는 경로/파일명에 유니코드(한글 등)이 섞인 경우 읽어오지 못함.
    여기서 유니코드 처리를 해주고 numpy 배열로 읽어서 돌려주기
    :param uni_filename: 유니코드로 된 파일명
    :param flags: cv2로 이미지를 읽을 때 gray로 읽을지, color로 읽을 지(기본값 = color)
    :param dtype: 어떤 인코딩 타입인지 결정 (uint8=unicode)
    :return: 읽어온 이미지 배열 객체 OR None
    """
    try:
        # 파일에서 uint8로 읽기
        n = np.fromfile(uni_filename, dtype)
        # unicode 파일을 디코드 해주기
        img = cv2.imdecode(n, flags)
        return img
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        traceback.print_stack()
        return None


def write_unicode_img(filename, img, params=None):
    """
    cv2의 imread 함수는 경로/파일명에 유니코드(한글 등)이 섞인 경우 읽어오지 못함.
    여기서 유니코드 인코딩 후 파일 저장해주기
    :param filename: 유니코드로 된 파일명
    :param img: 유니코드로 인코딩할 이미지 객체
    :param params: imdecode 함수에 들어갈 파라미터들, 기본값=None
    :return: 읽어온 이미지 배열 객체 OR None
    """
    try:
        # 확장자 제외 파일명 추출
        ext = os.path.splitext(filename)[1]
        # 인코딩 수행 (result = success, flag, n=인코딩 된 배열)
        result, n = cv2.imencode(ext, img, params)

        # 만일 성공했다면
        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
        return True
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        traceback.print_stack()
        return False
