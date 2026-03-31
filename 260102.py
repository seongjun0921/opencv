
# range()
# range(100)
# range(0, 100)
# range(0, 100, 2)

# for i in range(5):
#     print(str(i) + "=반복 변수")
# print()
#
# for i in range(5, 10):
#     print(str(i) + "=반복 변수")
# print()
#
# for i in range(5, 10, 3):
#     print(str(i) + "=반복 변수")
# print()

# output = ""
# for i in range(1, 10):
#     for j in range(0, i):
#         output += "*"
#     output +="\n"

# output = ""
# a = int(input("숫자 입력"))
# for i in range(0, a):
#     for j in range(0, a):
#         output += '#'
#     for k in range(1, i):
#         output += '*'
#     output +='\n'
#
# print(output)

# import time
# number = 0
#
# target_tick = time.time() + 5
# while time.time() < target_tick:
#     number += 1
# print("5초동안 {}번 반복했습니다.".format(number))

# key_list = ["name", "hp", "mp", "level"]
# value_list = ["기사", 200, 30, 5]
# character = {}
# for i in range(4):
#     character[key_list[i]] = value_list[i]
# print(character)


# limit = 10000
# i = 1
# sum_value = 0
# while i <= limit:
#     if i <= 141:
#         sum_value += i
#         i += 1
#     else:
#         break
# print("{}를 더할 때 {}을 넘으며 그때의 값은 {}입니다.".format(i-1, limit, sum_value))


# max_value = 0
# a = 0
# b = 0
# max_value = 0
#
# for i in range(1, 100):
#     j = 100 - i
#
#     if max_value < i*j:
#         max_value = i*j
#         a = i
#         b = j
#     else:
#         max_value = max_value
#         a = i
#         b = j
#
#
# print("chleork 되는 경우:{} * {} = {}".format(a, b, max_value))

# temp = reversed([1, 2, 3, 4, 5, 9])
#
# for i in temp:
#     print("첫 번째 반복문: {}".format(i))
#
# for i in temp:
#     print("첫 번째 반복문: {}".format(i))

# example_list = ["요소A", "요소B", "요소C"]
#
# print("#단순 출력")
# print(example_list)
# print()
#
# print("# enumerate() 함수적용 출력")
# print(enumerate(example_list))
# print()
#
# for i, value in enumerate(example_list):
# print("# list() 함수로 강제 변환 출력")
# print(list(enumerate(example_list)))
# print()
#
# print("#반복문과 조합하기")
#     print("{}번째 요소는 {}입니다".format(i, value))

# list_a = [1, 2, 3, 4, 1, 2, 3, 1, 4, 1, 2, 3]
# dict_a = {}
#
# for i in list_a:
#     if i not in dict_a:
#         dict_a[i] = 1
#     else:
#         dct_a[i] +=1
# print(dict_a)
# i

# list_b = input("염기 서열 입력해주세요")
#
# print(list_b.count("a"))
# print(list_b.count("t"))
# print(list_b.count("g"))
# print(list_b.count("c"))


# list_c = input("")
# codon = ""
# for i in range(len(list_c)):
#     if i % 3 == 0:
#         pass
#     else:
#         pass
#
# def print_n_times(n, *values):
#
#     for i in range(n):
#
#         for value in values:
#             print(value)
#
#         print()
# print_n_times(3, "안녕하세요", "즐거운", "파이썬 프로그래밍")

# def f(x):
#     return 2*x + 1
# print(f(10))
#
# def f(x):
#     return x * x + 2 * x + 1
# print(f(10))
#

# def power(item):
#     return item * item
# def under_3(item):
#     return item < 3
#
# list_input_a = [1, 2, 3, 4, 5]
#
# output_a = map(power, list_input_a)
# print("# map() 함수의 실행")
# print("map(power, list_input_a):", output_a)
# print("map(power, list_input_a):", list(output_a))
# print()
#
# output_b = filter(under_3, list_input_a)
#
# print("#filter() 함수의 실행 결과")
# print("filter(under_3, list_input_a):", output_b)
# print("filter(under_3, list_input_a):", list(output_b))

#tax.txt 내 이상치 1개 적절한 대체값으로 처리
#파일 객체/ 문자열, 리스트 관련 함수 활용
#사용자 입력으로 세전 연봉을 받고 네이버 연봉계산기와 동일한 출력 구조 구현

rows = []

with open("C:\\Users\\302-25\\Downloads\\tax.txt", "r") as file:
    for line in file:
        line = line.replace(",", "").replace("-", "")

        parts = line.split()

        row = [int(p.replace('"', '')) for p in parts if p.replace('"', '').isdigit()]

        if row:
            rows.append(row)

for col in range(2, max(len(r) for r in rows)):
    valid = [(i, rows[i][col]) for i in range(len(rows)) if len(rows[i]) > col]

    for k in range(1, len(valid) - 1):
        idx, cur = valid[k]
        prev = valid[k - 1][1]
        nxt  = valid[k + 1][1]

        if abs(cur - prev) >= 30000 and abs(cur - nxt) >= 30000:
            print(
                f" 오류 | 열={col+1} | 행={idx+1} | 값={cur} "
                f"| prev={prev}, next={nxt}"
            )



# a = int(input("연봉 입력"))
#
# b = a // 12
#
# c = b / 100 * 4.75
# print("국민연금 (4.75%): ", str(int(c)) + "원")
#
# d = b / 100 * 3.595
# print("건강보험 (3.595%): ", str(int(d)) + "원")
#
# e = d / 100 * 13.14
# e = e- e%10
# print("요양보험 (13.14%): ", str(int(e)) + "원")
#
# f = b / 100 * 0.9
# print("고용보험 (0.9%): ", str(int(f)) + "원")
#
# pay = b-c-d-e-f
# print("월 예상 실 수령액: ", str(int(pay)) + "원")
#
# d = b / 100 * 3.595
# print("근로소득세 (3.595%): ", str(int(d)) + "원")
