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
# 각 회사별 B/L 패턴 추출용
import re
# ocr된 dict를 텍스트 파일에 읽고 쓰기 위함
import ast

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
    # OCR 후 엑셀 저장 경로
    json_path = config_dict["OCR_Data"]
    # 데이터 검증 결과 저장용
    result_path = config_dict["Result"]
    # BL-회사 매핑 데이터 저장용
    bl_excel = config_dict["BL_Excel"]
    # 이미지 너비,높이 표준값 [width, height]
    resize_standard = [int(config_dict["Resize Standard Width"]),
                       int(config_dict["Resize Standard Height"])]
    # 필요 경로 생성
    Util.make_dir([original_path, formatted_path, result_path, json_path])

    # 업체별 좌표값 읽어오기 (파일이 있는 경우만, 없다면 좌표 지정 없이 풀텍스트 OCR
    bl_df = []
    if os.path.isfile(bl_excel):
        bl_df = pd.read_excel(bl_excel, 'BL_DICT')

    # pdf 포함 모든 파일들을 이미지로 변환하여 cleansed 경로로 이동
    Image_Controller.move_img(original_path, formatted_path)

    # 이미지 전처리 수행 (회전, 리사이즈)
    Image_Controller.cleanse_img(formatted_path, cleansed_path, resize_standard, bl_df)

    # OCR 자원 소모를 줄이기 위해, 일괄적으로 모든 이미지를 우선 ocr 처리
    # 이후 해당 텍스트 파일을 가지고 파싱 진행
    count = 0
    for cleansed_file in os.listdir(cleansed_path):
        base_filename = os.path.splitext(os.path.basename(cleansed_file))[0]
        # 경로인지 파일인지 탐색 및 경로면 넘어가기
        if os.path.isdir(cleansed_file):
            print(cleansed_file + "=경로입니다.")
            continue
        # 만일 이미 format 된 거면 넘어가기
        if Util.is_duplicated(base_filename, json_path):
            print("Already Converted to Text : ", cleansed_file)
            continue
        ocr_json = Cloud_Vision.detect_img_text(cleansed_path + cleansed_file)
        with io.open(json_path + base_filename + '.json', 'w', -1, 'utf-8') as f:
            f.write(str(ocr_json))
    
    # BL 번호 매칭 시 저장할 자료구조
    matched_file = []
    matched_company = []
    matched_bl = []

    for json_file in os.listdir(json_path):
        with open(json_path + json_file, 'r', -1, 'utf-8') as f:
            json_str = f.read()
            json = ast.literal_eval(json_str)

        base_filename = os.path.splitext(os.path.basename(json_file))[0]

        if len(json) < 1:
            print("OCR 실패 문서 발견: ", base_filename, ", json=", json)
            continue

        full_text = json["textAnnotations"][0]["description"]
        full_text_list = full_text.replace('\n', ' ')
        print(full_text_list)

        if "billoflading" not in full_text_list.lower().replace(' ', ''):
            print("B/L 문서가 아님: " + base_filename)
            continue

        # BL-회사 매핑 문서에서 회사명 리스트 추출
        company_list = list(bl_df["LogName_REGEX"])
        regex_list = list(bl_df["BL_REGEX"])
        # 저장용 변수 초기화
        temp_regex = None
        temp_c_name = None

        # 파일명 insert
        matched_file.append(base_filename)

        for c_name in company_list:
            if c_name in full_text_list:
                temp_c_name = c_name
                temp_regex = bl_df.loc[bl_df["LogName_REGEX"] == c_name]["BL_REGEX"].values[0]
                break

        # c_name이 없으면 애초에 회사명을 못 찾은 것
        if temp_c_name is None:
            matched_company.append("N/A")
        else:
            matched_company.append(temp_c_name)

        matched_list = []
        for c_regex in regex_list:
            # 이상한 정규표현식이면 무시
            if "str" not in str(type(c_regex)):
                # print("wrong regex=", c_regex, ", type=", type(c_regex))
                continue
            p = re.compile(c_regex)
            m = p.search(full_text_list)

            if m is not None:
                matched_list.append(m.group(0))
        matched_bl.append(matched_list)

    print("file=", len(matched_file), ", com=", len(matched_company), ", bl=", len(matched_bl))

    bl_matched = pd.DataFrame({
        "file": matched_file,
        "company": matched_company,
        "B/L": matched_bl
    })

    # STRICT 룰 적용 - 코드 수시 변경 가능
    for index in range(0, len(bl_matched["file"])):

        if bl_matched["company"][index] == "CONNECTION, INT" \
                or bl_matched["company"][index] == "CONNECTION INTERNATIONAL":
            bl_matched["B/L"][index] = ["PCI" + x[3:len(x)] for x in bl_matched["B/L"][index]]
            print(bl_matched["B/L"][index])

        if bl_matched["company"][index] == "H & FRIENDS":
            bl_matched["B/L"][index] = ["HFI" + x[3:len(x)] for x in bl_matched["B/L"][index]]
            print(bl_matched["B/L"][index])

        # -, whitespace 는 공통적으로 없애줘야 함
        bl_matched["B/L"][index] = [x.replace("-", "") for x in bl_matched["B/L"][index]]
        bl_matched["B/L"][index] = [x.replace(" ", "") for x in bl_matched["B/L"][index]]

        # 중복 제거
        bl_matched["B/L"][index] = list(set(bl_matched["B/L"][index]))
        # 1줄로 만들기
        bl_matched["B/L"][index] = ','.join(bl_matched["B/L"][index])

    bl_matched.to_excel(result_path + 'Matched_BL.xlsx', index=False)
