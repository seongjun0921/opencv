import tkinter
import pandas as pd
import numpy as np
import random
import seaborn as sns
import tkinter
import copy

df = pd.read_csv('min.csv', encoding='CP949')

df['현재인원'] = np.random.randint(1, 1001, size=len(df))

dff = df.drop(columns=['개방자치단체코드', '관리번호', '데이터갱신구분', '지정일자', '최종수정시점', '위도(분)', '위도(도)', '위도(초)',
                       '경도(도)', '데이터갱신시점', '해제일자', '소재지전체주소', '도로명우편번호', '경도(분)', '경도(초)', '위도(EPSG4326)',
                       '경도(EPSG4326)', '좌표정보X(EPSG5179)',
                       '좌표정보Y(EPSG5179)', '해제일자', '운영상태', '시설명', '도로명전체주소'])

srh = df.drop(columns=['개방자치단체코드', '관리번호', '데이터갱신구분', '지정일자', '시설구분', '최종수정시점', '위도(분)', '위도(도)', '위도(초)',
                       '경도(도)', '데이터갱신시점', '해제일자', '소재지전체주소', '도로명우편번호', '경도(분)', '경도(초)', '위도(EPSG4326)',
                       '경도(EPSG4326)', '좌표정보X(EPSG5179)',
                       '좌표정보Y(EPSG5179)', '해제일자', '운영상태', '시설명', '도로명전체주소'])

# 파생변수 생성
dff['수용가능인원'] = dff['최대수용인원'] - dff['현재인원']
dff = dff.assign( 크기=np.where(dff['시설면적(㎡)'] > 80000, 'Large', np.where(dff['시설면적(㎡)'] > 8000, 'Medium', 'Small')))
#
# dfff = dff.query('`시설위치(지상/지하)` == "지상"')['시설위치(지상/지하)']
# print(dfff)

def apply_filter():
    df_filter = copy.deepcopy(dff)

    #시설구분
    loc_values = []
    if CheckVariety_1.get() == 1:
        loc_values.append("지상")
    if CheckVariety_2.get() == 1:
        loc_values.append("지하")

    if loc_values:
        df_filter = df_filter[
            df_filter['시설위치(지상/지하)'].isin(loc_values)
        ]

    type_values = []
    if CheckVariety_3.get() == 1:
        type_values.append("공공용시설")
    if CheckVariety_4.get() == 1:
        type_values.append("정부지원시설")

    if type_values:
        df_filter = df_filter[df_filter['시설구분'].isin(type_values)]

    result_label.config(text=df_filter)

import tkinter

window=tkinter.Tk()
window.title("YUN DAE HEE")
window.geometry("640x480+100+100")
window.resizable(False, False)

result_label = tkinter.Label(window, text="")
result_label.pack()

CheckVariety_1=tkinter.IntVar()
CheckVariety_2=tkinter.IntVar()
CheckVariety_3=tkinter.IntVar()
CheckVariety_4=tkinter.IntVar()
checkbutton1=tkinter.Checkbutton(window, text="지상", variable=CheckVariety_1 )
checkbutton2=tkinter.Checkbutton(window, text="지하", variable=CheckVariety_2)
checkbutton3=tkinter.Checkbutton(window, text="공공용시설", variable=CheckVariety_3)
checkbutton4=tkinter.Checkbutton(window, text="정부지원시설", variable=CheckVariety_4)

tkinter.Button(window, text="필터 적용", command= apply_filter).pack()


checkbutton1.pack()
checkbutton2.pack()
checkbutton3.pack()
checkbutton4.pack()

window.mainloop()


dfff = df.loc[df['시설위치(지상/지하)'] == '지상']
print(dfff['시설위치(지상/지하)'])
