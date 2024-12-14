import time
import pandas as pd
import numpy as np
import shutil
from src.basicFunction import *

CSV_COLUMNS = ['날짜', '차량번호', '차종', '세차종류', '금액', '결제방법', '비고']
CAR_WASH_OPTIONS = ['노터치', '외', '내', '폼', '발수', '광택', '왁스', '타르', '석회']
RECENT_NUMBER = 20


def data_reorganize(data, sort_method):
    if sort_method == '인덱스':
        data_sort = data.sort_index(ascending=False)
    else:
        data_sort = data.sort_values(by=[sort_method], ascending=False)
    data_sort = data_sort.reset_index(drop=True)
    data_sort.loc[data_sort['금액'] == '공짜', '금액'] = '0'
    data_sort.loc[data_sort['금액'] == '없음', '금액'] = '0'
    return data_sort


def load_filtered_data(filepath, car_number, car_type, remark_search, search_start, search_end, pay_options):
    if isfile_and_pass(filepath):
        data = pd.read_csv(filepath, dtype=object, encoding='cp949')
        data = data.fillna('없음')
        df_car_rev_list, car_number_list = filter_by_search(data, car_number, car_type, remark_search, search_start, search_end, pay_options)
    else:
        data_car_rev = pd.DataFrame(columns=CSV_COLUMNS)
        df_car_rev_list = [data_car_rev]
        car_number_list = ['파일 없음']
    return df_car_rev_list, car_number_list


def search_by_date(df, start, end):
    if start == '': start = '2020-08-01'
    return df[df['날짜'].between(start, end)]


def filter_by_search(data, car_number, car_type, remark_search, search_start, search_end, pay_options):
    data_type = data[data['차종'].str.contains(car_type)]
    data_remark = data_type[data_type['비고'].str.contains(remark_search)]
    data_remark_date = search_by_date(data_remark, search_start, search_end)

    if len(pay_options) != 0:
        str_pay_contain = '|'.join(pay_options)
        data_option = data_remark_date[data_remark_date['결제방법'].str.contains(str_pay_contain)]
    else:
        data_option = data_remark_date

    data_car = data_option[data_option['차량번호'].str.contains(car_number)]

    car_number_list = []
    df_car_list = []
    df_car_rev_list = []

    if data_car.empty:
        df_car_rev_list.append(data_car)
        car_number_list.append('데이터 검색 결과 없음')
    else:
        if car_number == '':
            df_car_list.append(data_car)
            car_number_list.append('번호 전체 검색')
        else:
            data_car_grouped = data_car.groupby('차량번호')
            for name, group in data_car_grouped:
                car_number_list.append(name)
                df_car_list.append(group)

        for df_car in df_car_list:
            data_car_sort = data_reorganize(df_car, '날짜')
            cost_sum = '{0:,}'.format(data_car_sort["금액"].str.replace(',', '').astype(int).sum())
            df_sum = pd.DataFrame([['총횟수', '{}번'.format(len(data_car_sort)), '', '총금액', cost_sum, '', '']], columns=CSV_COLUMNS)
            data_car_rev = pd.concat([df_sum, data_car_sort], axis=0).reset_index(drop=True)
            df_car_rev_list.append(data_car_rev)

    return df_car_rev_list, car_number_list


def save_input_data(filepath, car_number, car_type, wash_option, cost, pay_option, remark_word):
    time_var = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    str_car_number = car_number.replace(" ", "")
    str_car_type = car_type.replace(" ", "")

    str_cost = cost.replace(" ", "")
    if str_cost == "":
        str_cost = '0'
    try:
        str_cost = '{0:,}'.format(int(str_cost) * 1000)
    except:
        str_cost = '0'

    str_wash_option = ", ".join(wash_option)
    if str_wash_option == "":
        str_wash_option = "없음"

    str_pay_option = ", ".join(pay_option)
    if str_pay_option == "":
        str_pay_option = "없음"

    if remark_word == "":
        str_remark_word = "없음"
    else:
        str_remark_word = remark_word

    df_input = pd.DataFrame([[time_var, str_car_number, str_car_type, str_wash_option, str_cost, str_pay_option, str_remark_word]],
                            columns=CSV_COLUMNS)

    if isfile_and_pass(filepath):
        data_origin = pd.read_csv(filepath, dtype=object, encoding='cp949')
        data = pd.concat([data_origin, df_input], axis=0).reset_index(drop=True)
        data.to_csv(filepath, encoding='cp949', index=False)
    else:
        df_input.to_csv(filepath, encoding='cp949', index=False)

    return df_input


def load_recent_data(filepath):
    if isfile_and_pass(filepath):
        data = pd.read_csv(filepath, dtype=object, encoding='cp949')
        data = data.fillna('없음')
        data_sort = data_reorganize(data, '인덱스')
        df_car_rev_list = [data_sort.head(RECENT_NUMBER)]
        car_number_list = ['최근 기록 20개 이하']
    else:
        data_car_rev = pd.DataFrame(columns=CSV_COLUMNS)
        df_car_rev_list = [data_car_rev]
        car_number_list = ['파일 없음']
    return df_car_rev_list, car_number_list


def remove_previous_data(filepath):
    if isfile_and_pass(filepath):
        data = pd.read_csv(filepath, dtype=object, encoding='cp949')
        data_last = data.iloc[-1:]
        data_rev = data[:-1].reset_index(drop=True)
        data_rev.to_csv(filepath, encoding='cp949', index=False)
        return data_last.values.tolist()


def calculate_revenue(data_origin, period):
    data_sort = data_reorganize(data_origin, '날짜')
    data_sort["금액"] = data_sort["금액"].str.replace(',', '').astype(int)
    data_sort['날짜'] = pd.to_datetime(data_sort['날짜'])
    data_sort.set_index(data_sort['날짜'], inplace=True)
    data_sort_resample = data_sort.resample(period)['금액'].sum().fillna(0)

    df_sort = pd.DataFrame({'날짜': data_sort_resample.index, '금액': data_sort_resample.values})
    df_sort["금액"] = df_sort["금액"] / 1000

    if period == 'ME':
        df_sort['날짜'] = df_sort['날짜'].map(lambda x: str(x.year) + '-' + str(x.month).rjust(2, '0'))
    else:
        df_sort['날짜'] = df_sort['날짜'].dt.strftime('%Y-%m-%d')

    return df_sort, df_sort["금액"].sum()


def calculate_revenue_ratio(data_origin):
    revenue_cnt = []
    df_copy = data_origin.copy()
    for option in CAR_WASH_OPTIONS:
        temp_data = data_origin[data_origin['세차종류'].str.contains(option)]
        df_copy = df_copy[df_copy["세차종류"].str.contains(option, na=False) == False]
        revenue_cnt.append(len(temp_data))
    revenue_cnt.append(len(df_copy))
    df_revenue_ratio = pd.DataFrame({'종류': CAR_WASH_OPTIONS + ['기타'], '횟수': revenue_cnt})
    return df_revenue_ratio


def update_file(temp_path, file_path):
    files = [os.path.join(temp_path, f_name) for f_name in os.listdir(temp_path) if 'xlsx' in f_name]
    if files:
        recent_file = max(files, key=os.path.getmtime)
        shutil.move(recent_file, os.path.join(temp_path, '컴인워시_작업일지.xlsx'))
        df_work_log = pd.read_excel(os.path.join(temp_path, '컴인워시_작업일지.xlsx'))

        shutil.move(file_path, os.path.join(temp_path, '컴인워시_작업일지_백업.csv'))  # 백업 파일
        df_work_log.to_csv(file_path, encoding='cp949', index=False)
