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
