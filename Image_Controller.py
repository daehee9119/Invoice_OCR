import os
import shutil
from pdf2image import convert_from_path


def move_img(original_path, target_path, cleansed_list):
    """
    original_path 경로에 있는 pdf 파일/이미지 파일들을 target_path에 온전히 이미지 파일로만 적재
    :param original_path: Invoice 원본이 적재된 경로
    :param target_path: pdf를 이미지로 변환하여 적재할 경로 (원본 이미지의 경우 그대로 복사하여 이 경로로 이동)
    :param cleansed_list: 이미 작업 경로에 존재하는 파일들
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
        for cleansed_item in cleansed_list:
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
