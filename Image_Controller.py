import os
import shutil
# pdf를 이미지로 변환하기 위한 패키지
from pdf2image import convert_from_path
# 이미지 슬라이싱을 위한 패키지들
import numpy as np
import PIL.Image as pilimg
# 이미지 회전을 위한 패키지들
import cv2
from scipy import ndimage
import statistics
import math


def move_img(original_path, target_path, formatted_list):
    """
    original_path 경로에 있는 pdf 파일/이미지 파일들을 target_path에 온전히 이미지 파일로만 적재
    :param original_path: Invoice 원본이 적재된 경로
    :param target_path: pdf를 이미지로 변환하여 적재할 경로 (원본 이미지의 경우 그대로 복사하여 이 경로로 이동)
    :param formatted_list: 이미 정제가 끝난 파일들
    :return: None
    """
    for filename in os.listdir(original_path):
        # 경로인지 파일인지 탐색 및 경로면 넘어가기
        if os.path.isdir(filename):
            print(filename + "=경로입니다.")
            continue

        # 파일명 이미 존재 시 해당 파일은 이동/pdf 이미지 변환에서 제외
        base_filename = os.path.splitext(os.path.basename(filename))[0]
        existed = False
        for cleansed_item in formatted_list:
            if base_filename in cleansed_item:
                existed = True
                break
        if existed is True:
            print("Already Cleansed : ", base_filename)
            continue

        # 파일 형식이 pdf면 pdf를 이미지로 변환
        if filename.lower().endswith('.pdf'):
            print("PDF 이미지화: ", filename)
            pdf_to_image(original_path, filename, target_path)
        # 이미지 형식이면 복사
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            shutil.copy(original_path + filename, target_path + filename)
        # 지정된 형식이 아닐 경우 넘어가기
        else:
            print(filename + ': 지정되지 않은 형식. .pdf, .png, .jpg, .jpeg 가 아니면 안됩니다.')


def pdf_to_image(path, filename, save_dir):
    """
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
                page.save(os.path.join(save_dir, base_filename) + '(' + str(page_count) + ').jpg', 'JPEG')
                page_count += 1

    except Exception as ex:
        print("PDF 파일을 이미지로 변환하는데 실패했습니다: " + filename + " -> {}".format(ex))
        # 혹시 일부가 이미 이미지로 변환되었다면 해당 파일을 모두 지울 것
        for img in os.listdir(save_dir):
            if base_filename in img:
                os.remove(path + img)


def cleanse_img(formatted_path):
    """
    이미지 전처리 수행(이미지 회전 & 이미지 리사이징)
    :param formatted_path: 전처리 대상 파일들
    :return: None
    """


def resize_image(path, filename):
    """
    모든 이미지는 A4 규격()으로 리사이징
    :param path: 리사이징할 파일이 속한 경로
    :param filename: 리사이징할 파일명
    :return: None
    """


def rotate_image(path, filename):
    """
    cv2의 허프 변환 함수를 이용해 이미지의 회전 여부 파악 및 0.1도 이상 회전 시 변환
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



def crop_image(formatted_path, save_dir, coord_dict):
    """
    지정된 이미지를 순회하면서 정해진 좌표에 기반하여 특정 영역 추출 및 저장
    :param formatted_path: 잘라낼 원본 이미지 저장 경로
    :param save_dir: 전처리 후 이미지 저장할 경로
    :param coord_dict: 파일들 중 일부는 특정 영역만 잘라서 저장해야 함
    :return: None
    """
    existed = False
    for org_filename in os.listdir(formatted_path):
        # 좌표를 가졌는지 판단하는 플래그
        is_target = False
        # 좌표가 있는 경우 해당 행의 인덱스를 담기 위한 변수
        target_index = None
        # 좌표 리스트를 순회
        for index in range(0, len(coord_dict)):
            # 만일 대상이 맞다면 플래그 true 찍고 좌표값 추출 및 break
            if coord_dict.loc[index, "PtrName"] in org_filename:
                is_target = True
                target_index = index
                break
        
        # 좌표값이 존재하는 이미지는 정제 후 다른이름 저장
        if is_target is True:
            img = pilimg.open(formatted_path + org_filename)
            img_array = np.array(img)
            # pixel 배열을 슬라이스하여 이미지 자르기
            cropped_img = img_array[
                          coord_dict.loc[target_index, "Y1"]:coord_dict.loc[target_index, "Y2"] + 1,
                          coord_dict.loc[target_index, "X1"]:coord_dict.loc[target_index, "X2"] + 1,
                          :
                          ]
            cropped_img = pilimg.fromarray(cropped_img.astype('uint8'), 'RGB')
            cropped_img.save(save_dir + org_filename)
        # 좌표값이 없는 이미지는 그대로 복사하여 다른 이름 저장
        else:
            shutil.copy(formatted_path + org_filename, save_dir + org_filename)
