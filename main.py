from fastapi import FastAPI, Form, Request, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from werkzeug.utils import secure_filename
from datetime import datetime
from src.dataProcess import *
import uvicorn


app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


class Global:
    period = 'ME'


class WorkLog:
    # filepath = r'C:\Users\이영희\Desktop\컴인워시작업일지'
    filepath = r'C:\Users\yongh\PycharmProjects\webApp\data'
    backup_filepath = r'C:\컴인워시_백업\컴인워시_작업일지.csv'


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    print(BRIGHT_YELLOW + "알림: 홈 페이지 접속\n" + BRIGHT_END)
    return templates.TemplateResponse(request=request, name='home.html', context={'current_date': datetime.now().strftime('%Y-%m-%d')})


@app.get('/input', response_class=HTMLResponse)
async def write_csv(request: Request):
    print(BRIGHT_YELLOW + "알림: 입력 페이지 접속\n" + BRIGHT_END)
    return templates.TemplateResponse(request=request, name='input.html', context={'file_close': is_file_close('컴인워시_작업일지')})


@app.post('/input_data')
async def save_data(car_number: str = Form(''),
                    car_name: str = Form(''),
                    wash_option: str = Form(''),
                    pay_option: str = Form(''),
                    cost: str = Form(''),
                    remark_word: str = Form('')):
    print("입력 데이터\n"
          "차량 번호: {number}, 차량 종류: {name}, 세자 종류: {wash}\n"
          "결제 방식: {option}, 금액: {cost}, 비고: {remark}\n"
          .format(number=car_number, name=car_name, wash=wash_option, option=pay_option, cost=cost, remark=remark_word))
    save_input_data(WorkLog.backup_filepath, car_number, car_name, wash_option, cost, pay_option, remark_word)
    return RedirectResponse(url='/input', status_code=status.HTTP_302_FOUND)


@app.post('/data')
async def display_filtered_data(request: Request,
                                car_number: str = Form(''),
                                car_type: str = Form(''),
                                remark_word: str = Form(''),
                                start_date: str = Form(''),
                                end_date: str = Form(''),
                                pay_option: str = Form('')):
    print("검색 데이터\n"
          "차량 번호: {number}\n"
          "차량 종류: {car_type}, 비고: {remark}\n"
          "시작 날짜: {start}, 끝 날짜: {end}\n"
          "결제 방식: {option}\n"
          .format(number=car_number, car_type=car_type, remark=remark_word, start=start_date, end=end_date, option=pay_option))
    data_list, name_list = load_filtered_data(WorkLog.backup_filepath, car_number, car_type, remark_word, start_date, end_date, pay_option)
    tables = [data.to_html(classes='blue_data') for data in data_list]
    print("검색 번호 리스트\n{}\n".format(name_list))
    return templates.TemplateResponse(request=request, name='table.html', context={'tables': tables, 'titles': name_list})


@app.get('/recent_data', response_class=HTMLResponse)
async def display_recent_data(request: Request):
    print(BRIGHT_YELLOW + "알림: 최근 데이터 조회 접속\n" + BRIGHT_END)
    data_list, name_list = load_recent_data(WorkLog.backup_filepath)
    tables = [data.to_html(classes='blue_data') for data in data_list]
    return templates.TemplateResponse(request=request, name='table.html', context={'tables': tables, 'titles': name_list})


@app.get('/delete_data')
async def delete_previous_data():
    if is_file_close('컴인워시_작업일지') != 'Open':
        data_last = remove_previous_data(WorkLog.backup_filepath)
        print(BRIGHT_GREEN + "성공: 직전 데이터 삭제\n{}\n".format(data_last) + BRIGHT_END)
    return RedirectResponse(url='/recent_data', status_code=status.HTTP_302_FOUND)


@app.post("/revenue")
async def display_revenue(request: Request, period: str = Form('')):
    # Generate the figure **without using pyplot**.
    data = pd.read_csv(WorkLog.backup_filepath, dtype=object, encoding='cp949')
    Global.period = period
    end_date = datetime.now().strftime('%Y-%m-%d')

    if Global.period == 'Ratio':
        print(BRIGHT_YELLOW + "알림: 매출 비율 보기 접속\n" + BRIGHT_END)
        revenue_cnt = calculate_revenue_ratio(data)
        background_color = ['rgba(75, 192, 192, 0.2)', 'rgba(204, 51, 51, 0.2)', 'rgba(0, 51, 153, 0.2)',
                            'rgba(204, 255, 0, 0.2)',
                            'rgba(255, 153, 0, 0.2)', 'rgba(153, 0, 204, 0.2)', 'rgba(0, 102, 153, 0.2)',
                            'rgba(153, 204, 153, 0.2)',
                            'rgba(102, 0, 0, 0.2)', 'rgba(0, 0, 0, 0.2)']

        return templates.TemplateResponse(request=request, name='chart.html',
                                          context={'x_data': revenue_cnt['종류'].values.tolist(),
                                                   'y_data': revenue_cnt['횟수'].values.tolist(),
                                                   'background': background_color,
                                                   'title_str': '매출 비율',
                                                   'ylabel_str': '횟수',
                                                   'current_date': end_date})
    else:
        if Global.period == 'ME':
            title = '월별 매출 그래프'
            print(BRIGHT_YELLOW + "알림: 월별 매출 보기 접속\n" + BRIGHT_END)
        elif Global.period == 'W-MON':
            title = '주별 매출 그래프'
            print(BRIGHT_YELLOW + "알림: 주별 매출 보기 접속\n" + BRIGHT_END)
        else:
            title = '일별 매출 그래프'
            print(BRIGHT_YELLOW + "알림: 일별 매출 보기 접속\n" + BRIGHT_END)
        data_period, cost_sum = calculate_revenue(data, Global.period)
        total_revenue = ' [총 매출액: {0:,}(천원)]'.format(int(cost_sum))
        background_color = ['rgba(75, 192, 192, 0.2)' for _ in range(len(data_period))]
        return templates.TemplateResponse(request=request, name='chart.html',
                                          context={'x_data': data_period['날짜'].values.tolist(),
                                                   'y_data': data_period['금액'].values.tolist(),
                                                   'background': background_color,
                                                   'total_revenue': total_revenue,
                                                   'title_str': title,
                                                   'ylabel_str': '매출액(천원)',
                                                   'current_date': end_date})


@app.post('/period_revenue')
async def display_revenue_period(request: Request, start_period: str = Form(''), end_period: str = Form('')):
    print(BRIGHT_YELLOW + "알림: 매출액(기간 포함) 보기 접속\n" + BRIGHT_END)

    data_origin = pd.read_csv(WorkLog.backup_filepath, dtype=object, encoding='cp949')
    data = search_by_date(data_origin, start_period, end_period)

    if Global.period == 'Ratio':
        revenue_cnt = calculate_revenue_ratio(data)
        background_color = ['rgba(75, 192, 192, 0.2)', 'rgba(204, 51, 51, 0.2)', 'rgba(0, 51, 153, 0.2)',
                            'rgba(204, 255, 0, 0.2)',
                            'rgba(255, 153, 0, 0.2)', 'rgba(153, 0, 204, 0.2)', 'rgba(0, 102, 153, 0.2)',
                            'rgba(153, 204, 153, 0.2)',
                            'rgba(102, 0, 0, 0.2)', 'rgba(0, 0, 0, 0.2)']
        return templates.TemplateResponse(request=request, name='chart.html',
                                          context={'x_data': revenue_cnt['종류'].values.tolist(),
                                                   'y_data': revenue_cnt['횟수'].values.tolist(),
                                                   'background': background_color,
                                                   'title_str': '매출 비율',
                                                   'ylabel_str': '횟수',
                                                   'start_date': start_period,
                                                   'current_date': end_period})
    else:
        if Global.period == 'ME':
            title = '월별 총 매출액'
        elif Global.period == 'W-MON':
            title = '주별 총 매출액'
        else:
            title = '일별 총 매출액'
        data_period, cost_sum = calculate_revenue(data, Global.period)
        total_revenue = ' [총 매출액: {0:,}(천원)]'.format(int(cost_sum))
        background_color = ['rgba(75, 192, 192, 0.2)' for _ in range(len(data_period))]
        return templates.TemplateResponse(request=request, name='chart.html',
                                          context={'x_data': data_period['날짜'].values.tolist(),
                                                   'y_data': data_period['금액'].values.tolist(),
                                                   'background': background_color,
                                                   'total_revenue': total_revenue,
                                                   'title_str': title,
                                                   'ylabel_str': '매출액(천원)',
                                                   'start_date': start_period,
                                                   'current_date': end_period})


@app.get('/work_log', response_class=HTMLResponse)
async def work_log(request: Request):
    print(BRIGHT_YELLOW + "알림: 작업 일지 페이지 접속\n" + BRIGHT_END)
    return templates.TemplateResponse(request=request, name='work.html', context={'file_exist': is_file_exist(WorkLog.backup_filepath)})


@app.get('/download')
async def download_file():
    r_csv = pd.read_csv(WorkLog.backup_filepath, dtype=object, encoding='cp949')
    save_xlsx = pd.ExcelWriter("./data/컴인워시_작업일지.xlsx")
    r_csv.to_excel(save_xlsx, index=False)  # xlsx 파일로 변환
    save_xlsx.close()  # xlsx 파일로 저장
    return FileResponse(path="./data/컴인워시_작업일지.xlsx", media_type='application/x-xlsx', filename="컴인워시_작업일지.xlsx")


@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    file_path = os.path.join('./data', secure_filename(file.filename))
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    update_file('./data', WorkLog.backup_filepath)
    return templates.TemplateResponse(request=request, name='work.html', context={'file_exist': 'Success'})


if __name__ == '__main__':
    import socket
    ipv4 = socket.gethostbyname(socket.gethostname())

    print(BRIGHT_GREEN + '***********************************************************' + BRIGHT_END)
    print(BRIGHT_GREEN + '*                 ' + BRIGHT_CYAN + '컴인워시 프로그램 시작' + BRIGHT_GREEN + '                  *' + BRIGHT_END)
    print(BRIGHT_GREEN + '*                                                         *' + BRIGHT_END)
    print(BRIGHT_GREEN + '*                   ' + BRIGHT_CYAN + '모바일 폰 접속 가능' + BRIGHT_GREEN + '                   *' + BRIGHT_END)
    print(BRIGHT_GREEN + '***********************************************************\n' + BRIGHT_END)

    print(BRIGHT_RED + '***********************************************************' + BRIGHT_END)
    print(BRIGHT_RED + ' 해당 주소 ' + BRIGHT_BLUE + 'http://{}:5000'.format(ipv4) + BRIGHT_RED + ' 를 통해 접속 하세요' + BRIGHT_END)
    print(BRIGHT_RED + '***********************************************************\n' + BRIGHT_END)

    logging_initialize()

    uvicorn.run(app, host=ipv4, port=5000)
