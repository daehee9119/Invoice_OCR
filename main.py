import os
import io
# config 파일 내 설정 정보 가져올 때 쓰임
import configparser
# 이미지 관련 util 함수를 모아둔 스크립트
import Image_Controller
# 구글 클라우드 vision api 호출 함수를 모아둔 스크립트
import Cloud_Vision
# OS 관련 일을 처리할 함수를 모아둔 스크립트
import Util
# 예외 처리용 패키지
import traceback
# 엑셀 데이터를 가져와 관리할 용도
import pandas as pd

# ######################MAIN STREAM###################### #
if __name__ == '__main__':

    # ini 파일 데이터를 적재할 config 객체 생성
    config_dict = ''
    try:
        # ini 파일 읽기
        config = configparser.ConfigParser()
        config.read('./config/Invoice_OCR.ini')
        config_dict = config[os.path.relpath(__file__)]
    except IOError as e:
        print("Failed to load Config File! (./config/Invoice_OCR.ini) ")
        traceback.print_stack()
        traceback.print_exc()
        # config 파일이 없으면 프로그램 그냥 종료해야 함
        exit(-1)

    # API 사용을 위한 인증 정보를 환경 변수에 설정
    # 그냥 환경변수에 설정하면 원인 모를 이유로 python 실행 시 가져오지 못함
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config_dict['API_KEY']

    # 원본 이미지, pdf 파일들을 모아두는 경로
    original_path = config_dict["Origin_Data"]
    # jpeg 로 모두 클린징한 invoice 를 모아두는 경로
    formatted_path = config_dict["Formatted_Data"]
    cleansed_path = config_dict["Cleansed_Data"]
    result_path = config_dict["Result"]
    coord_excel = config_dict["Coordinates Excel"]
    # 이미지 너비,높이 표준값 [width, height]
    resize_standard = [int(config_dict["Resize Standard Width"]),
                       int(config_dict["Resize Standard Height"])]
    # 필요 경로 생성
    Util.make_dir([original_path, formatted_path, result_path])

    # 업체별 좌표값 읽어오기 (파일이 있는 경우만, 없다면 좌표 지정 없이 풀텍스트 OCR
    coord_dict = ""
    if os.path.isfile(coord_excel):
        coord_dict = pd.read_excel(coord_excel, 'Coordinates')

    # pdf 포함 모든 파일들을 이미지로 변환하여 cleansed 경로로 이동
    Image_Controller.move_img(original_path, formatted_path)

    # 이미지 전처리 수행 (회전, 리사이즈)
    Image_Controller.cleanse_img(formatted_path, cleansed_path, resize_standard, coord_dict)

    # # 5개의 샘플만 시도
    # count = 0
    # for img_file in os.listdir(cleansed_path):
    #     if count > 5:
    #         break
    #     total_str = Cloud_Vision.detect_img_text(cleansed_path + img_file)
    #     with io.open(result_path + img_file + '_result.txt', 'w', encoding="utf-8") as f:
    #         f.write(total_str)
    #     count += 1
