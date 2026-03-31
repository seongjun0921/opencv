import tkinter

window=tkinter.Tk()
window.title("YUN DAE HEE")
window.geometry("640x400+100+100")
window.resizable(True, True)

width=1

def drawing(event):
    if width>0:
        x1=event.x-1
        y1=event.y-1
        x2=event.x+1
        y2=event.y+1
        canvas.create_oval(x1, y1, x2, y2, fill="blue", width=width)

def scroll(event):
    global width
    if event.delta==120:
        width+=1
    if event.delta==-120:
        width-=1
    label.config(text=str(width))

canvas=tkinter.Canvas(window, relief="solid", bd=2)
canvas.pack(expand=True, fill="both")
canvas.bind("<B1-Motion>", drawing)
canvas.bind("<MouseWheel>", scroll)

label=tkinter.Label(window, text=str(width))
label.pack()

window.mainloop()

# # a= 'aaa'
# # print(a.upper())
# # print(a)
# #
# # #숫자/ 문자/ 불/ 리스트/ 딕셔너리/ 세트/ 튜플
# # #불변 immutable : int, str, tuple
# # #가변 immutable : list, dict, set
# #
# # #sorted(list) : 정렬 리스트 반환
# # #list.sort() : 기존리스트 직접 정렬, 반환
# #
# #
# # print("asd{}asd".format(100))
# # print(f"asd{100}asd")
# #
# # r = int(input("구의 반지름을 입력해주세요: "))
# # print(f"구의 부피는 {4/3*3.14*r*r*r}입니다.")
# # print(f"구의 겉넓이는 {4*3.14*r*r}입니다.")
# #
# # x = float(input("밑변의 길이를 입력해주세요: "))
# # y = float(input("높이의 길이를 입력해주세요: "))
# #
# # print(f"빗변의 길이는{(x*x+y*y)**(1/2)}입니다.")
# #
# # #문자열.함수명() => object 기능 함수 호출 => 문자열 전용함수
# # #함수명(문자열) => 여러 object에서 사용 가능
# #
# # # == 두 값이 같은지
# # #is연산자: 메모리 주소 비교 => 두 대상이 동일한 메모리에 있는지
# #
# # #a = b =>b는 a의 메모리 주소를 복사
# #
# # x = 10
# # under_20 = x < 20
# # print("under_20:", under_20)
# # print("not under_20", not under_20)
# #
# # import datetime
# # now = datetime.datetime.now()
# # print(now.year, "년")
# # print(now.month, "월")
# # print(now.day, "일")
# # print(now.hour, "시")
# # print(now.minute, "분")
# # print(now.second, "초")
# #
# # # 리스트/딕셔너리/셋/튜플/문자열/range/
# #
# # list_of_list = [
# #     [1,2,3],
# #     [4,5,6,7],
# #     [8,9]
# # ]
# #
# # for items in list_of_list:
# #     for item in items:
# #         print(items)
# #
# # dictionary = {
# #     "name": "7D 건조 망고",
# #     "type": "당절임",
# #     "ingredient": ["망고", "설탕","메타중아황산나트륨", "치자황색소"],
# #     "origin": "필리핀"
# # }
# #
# # print("name", dictionary["name"])
# # print("type", dictionary["type"])
# # print("ingredient", dictionary["ingredient"])
# # print("origin", dictionary["origin"])
# # print()
# #
# # dictionary["name"] = "8D 건조 망고"
# # print("name: ", dictionary["name"])
#
# #
# # pets = [
# #     {"name": "구름", "age": 5},
# #     {"name": "초코", "age": 3},
# #     {"name": "아지", "age": 1},
# #     {"name": "호랑이", "age": 1},
# # ]
# #
# # print("# 우리 동네 애완 동물들")
# # age = "살"
# # for pet in pets:
# #     print(pet["name"], pet["age"],age)
# #
# #
# #
#
# # numbers = [1, 2, 6, 8, 4, 3, 2, 1, 9, 5, 4, 9, 7, 2, 1, 3, 5, 4, 8, 9, 7, 2, 3]
# # counter = {}
# #
# # for number in numbers:
# #     if counter.get(number):
# #         counter[number] += 1
# #     else:
# #         counter[number] = 1
# # print(counter)
#
#
# character = {
#     "name": "기사",
#     "level": 12,
#     "items": {
#         "sword": "불꽃의 검",
#         "armor": "풀플레이트"
#     },
#     "skill": ["베기", "세게 베기", "아주 세게 베기"]
# }
#
# for i in character:
#     if type(character[i]) == str:
#         print(f"{i}: {character[i]}")
#     elif type(character[i]) == int:
#         print(f"{i}: {character[i]}")
#     elif type(character[i]) == dict:
#         for j in character[i]:
#             print(f"{j}: {character[i][j]}")
#     else:
#         for k in character[i]:
#             print(f"{i}:{k}")