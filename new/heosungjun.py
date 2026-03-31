# #kime ~~ 영어 이름으로 모듈 이름 설정
# #if name != __main_- 활용 사용자에게 설명서 제공

#BMR(기초대사량) = (10 × 체중) + (6.25 × 신장) - (5 × 나이) + 5
#TDEE(활동대사량) = BMR × 활동 배수
# 운동거의 없음 1.2
# 가벼운 활동 1.375
# 보통 활동 1.55
# 매우 활동적 1.9
def Tdee(height, weight, age, act):
    bmr = int((6.25 * height) + (10 * weight) - (5 * age) + 5)
    tdee = bmr * act
    return height, weight, age, tdee
def health(weight, muscles, fat):
    fat_per = fat / weight * 100
    print(f"체지방률: {fat_per:.2f}")

    if weight < muscles + fat:
        print("잘못된 값 입력")

    else:
        if muscles >= (weight / 100 * 45) and (fat_per >= 18):
            print("다이어트 하세요")

        elif muscles >= (weight / 100 * 45) and (fat_per < 18):
            print("커팅 하세요")

        elif muscles < (weight / 100 * 45) and (fat_per < 18):
            print("벌크업 하세요")

        else:
            print("상승 다이어트 하세요")
    print()
def diet(tdee, day):
    if weight > goal:
        a = weight - goal
        day_a = 7700 * a / day
        tdee -= day_a
        print(f"빼야 할 몸무게: {a} kg")
        print(f"하루 적게 먹어야할 칼로리: {day_a:.2f} kcal")

    else:
        a = goal - weight
        day_a = 7700 * a / day
        tdee += day_a
        print(f"쪄야 할 몸무게: {a} kg")
        print(f"하루 더 먹어야할 칼로리: {day_a:.2f} kcal")
    print()

# def diet(weight, goal, day):
#     if weight > goal:
#         a = weight - goal
#         day_a = 7700 * a / day
#         print(f"빼야 할 몸무게: {a} kg")
#         print(f"하루 적게 먹어야할 칼로리: {day_a:.2f} kcal")
#
#     else:
#         a = goal - weight
#         day_a = 7700 * a / day
#         print(f"쪄야 할 몸무게: {a} kg")
#         print(f"하루 더 먹어야할 칼로리: {day_a:.2f} kcal")
#     print()

if __name__ == "__main__":
    print("# 함수설명 #")
    print()
    print("# health 함수설명: 매개변수(체중, 골격근량, 체지방량)를 토대로 운동방향 추천")
    print("# 골격근량 45% 이상 & 체지방률 18이상 --> 다이어트 하세요 출력")
    print("# 골격근량 45% 이상 & 체지방률 18이하 --> 커팅 하세요 출력")
    print("# 골격근량 45% 이하 & 체지방률 18이하 --> 벌크업 하세요 출력")
    print("# 골격근량 45% 이하 & 체지방률 18이상 --> 상승 다이어트 하세요 출력")
    print()
    print("# diet 함수: 매개변수(현재체중, 목표체중, 목표기간)를 받음")
    print("# 살을 빼는 것이 목표일시 유지칼로리 보다 적게 먹어야 할 하루칼로리 출력")
    print("# 살을 찌우는 것이 목표일시 유지칼로리 보다 많이 먹어야 할 하루칼로리 출력")