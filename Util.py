import os
import shutil
import traceback


def make_dir(dir_list):
    """
    경로 리스트를 배열로 받아 모두 만들어 줌. 없을때만 만들고 있으면 넘어감
    :param dir_list: 생성할 dir 리스트, 1개일 경우도 리스트 1개짜리로 만들어서 넣어줘야 함
    :return: none
    """
    for target_dir in dir_list:
        try:
            if not(os.path.isdir(target_dir)):
                os.makedirs(os.path.join(target_dir))
        except OSError as ex:
            print("Failed to create Dir! => ", target_dir, '\n', ex)
            traceback.print_stack()
            traceback.print_exc()
        finally:
            continue


def remove_dir(target_dir):
    """
    디렉토리가 존재하는 경우 해당 디렉토리 삭제
    그냥 해도 되긴 하는데..try catch로 따로 빼둠
    :param target_dir: 삭제할 디렉토리, abs나 rel 상관 없음
    :return: none
    """
    try:
        if os.path.isdir(target_dir):
            # rmtree를 써야 디렉토리 안에 파일까지 깔끔하게 날아감
            shutil.rmtree(target_dir)
    except OSError as ex:
        print("Failed to remove Dir! => ", target_dir, '\n', ex)
        traceback.print_stack()
        traceback.print_exc()


def is_duplicated(target_name, src_path):
    """
    특정 파일이 다른 경로 내 파일 리스트 이름에 포함되는지 확인
    :param target_name: 확인할 파일명
    :param src_path: 대조할 파일 리스트 경로
    :return: 존재 여부 boolean
    """
    # 확장자, 경로 제외한 순수 파일명
    base_filename = os.path.splitext(os.path.basename(target_name))[0]
    existed = False
    # 원본 경로를 순회하면서 base_filename이 src_item에 포함되는지 확인
    for src_item in os.listdir(src_path):
        if base_filename in src_item:
            existed = True
            break
    # 확인한 boolean 리턴
    return existed

