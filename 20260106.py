# from urllib import request
#
# headers = {'User-Agent': 'Mozilla/5.0(Windows Nt 10.0; Win64; x64)'
#            'AppleWebKit/537.36(KHTML, like Gecko)'
#            'Chrome/91.0.4472.124 Safari/537.36'
#            }
#
# url = "https://www.hanbit.co.kr/images/common/logo_hanbit.png"
# req = request.Request(url,headers=headers)
# target = request.urlopen(req)
# output = target.read()
# print(output)
# with open("output.png", "wb") as file:
#     file.write(output)

# class Student:
#     def __init__(self, name, korean, math, english, science):
#         self.name = name
#         self.korean = korean
#         self.math = math
#         self.english = english
#         self.science = science
# # self는 자기 자신을 의미
#
# def get_sum(self):
#     return self.korean + self.math +\
#         self.english + self.science
#
# def get_avg(self):
#     return self.get_sum() / 4
#
# def to_string(self):
#     return "{}\t{}\t{}".format(
#         self.name, \
#         self.get_sum(), \
#         self.get_avg())
# students = [
#     Student("윤희성", 87, 98, 88, 95),
#     Student("연하진", 92, 98, 96, 98),
#     Student("구지연", 76, 96, 94, 90),
#     Student("나선주", 98, 92, 96, 92),
#     Student("윤아린", 95, 98, 98, 98),
#     Student("윤명월", 64, 88, 92, 92)
# ]
#
# print("이름", "총점", "평균", sep="\t")
# for student in students:
#     print(student.to_string())
# students[0].name
# students[0].korean
# students[0].math
# students[0].english
# students[0].science
# print(students[0].math)

# class store:
#     def __init__(self, ):
#
# class Human:
#     def __intit__(self):
#         pass
# class Student(Human):
#     def __init__(self):
#         pass
#
# student = Student()
#
# print("isinstance(student, Human):", isinstance(student, Human))
# print("type(studenf) == Human:", type(student == Human))

# def __init__(self, name, korean, math, english, science):
#     self.name = name
#     self.korean = korean
#     self.math = math
#     self.english = english
#     self.science = science
#
#
# def get_sum(self):
#      return self.korean + self.math +\
#          self.english + self.science
#
#  def get_avg(self):
#      return self.get_sum() / 4
#
#  def __str__(self):
#      return "{}\t{}\t{}".format(
#          self.name,
#          self.get_sum(),
#          self.get_avg()
#      )
#
# students = [
#     Student("윤희성", 87, 98, 88, 95),
#     Student("연하진", 92, 98, 96, 98),
#     Student("구지연", 76, 96, 94, 90),
#     Student("나선주", 98, 92, 96, 92),
#     Student("윤아린", 95, 98, 98, 98),
#     Student("윤명월", 64, 88, 92, 92)
# ]
#
# print("이름", "총점", "평균", sep="\t")
# for student in students:
#     print(str(student))

# class Student:
#     count = 0
#     students = []
#
#     @classmethod
#     def print(cls):
#         print("------ 학생목록 ------")
#         print("이름\t총점\t평균")
#         for student in cls.students:
#             print(str(student))
#         print("------- ------- -------")
#
#     def __init__(self, name, korean,math, english, science ):
#         self.name = name
#         self.korean = korean
#         self.math = math
#         self.english = english
#         self.science = science
#         Student.count += 1
#         Student.students.append(self)
#
#     def get_sum(self):
#         return self.korean + self.math + self.english + self.science
#
#     def get_average(self):
#         return self.get_sum() / 4
#
#     def __str__(self):
#         return "{}\t{}\t{}".format(\
#             self.name,\
#             self.get_sum(),\
#             self.get_average())
#
# Student("윤희성", 87, 98, 88, 95)
# Student("연하진", 92, 98, 96, 98)
# Student("구지연", 76, 96, 94, 90)
# Student("나선주", 98, 92, 96, 92)
# Student("윤아린", 95, 98, 98, 98)
# Student("윤명월", 64, 88, 92, 92)
# Student("김미화", 82, 86, 98, 88)
# Student("김연화", 88, 74, 78, 92)
# Student("박아현", 97, 92, 88, 95)
# Student("서준서", 45, 52, 72, 78)
#
# Student.print()

# 프라이빗 변수 __변수명 형태로 외부에서 접근 불가
#priviate: 가려진 변수, 외부에서 볼 수 없음
#public: 공개 변수 인스턴스를 통해 볼 수 있음

# import math
# class Circle:
#     def __init__(self, radius):
#         self.__radius = radius
#     def get_circumference(self):
#         return 2 * math.pi * self.__radius
#     def get_area(self):
#         return math.pi * (self.__radius**2)
#
#     def get_radius(self):
#         return self.__radius
#     def set_radius(self, value):
#         self.__radius = value
#
# circle = Circle(10)
# print("#원의 둘레와 넓이를구합니다.")
# print("원의 둘레:", circle.get_circumference())
# print("원의 넓이:", circle.get_area())
# print()
#
# print("#__radius에 접근합니다.")
# print(circle.get_radius())
# print()
#
# circle.set_radius(2)
# print("#반지름을 변경하고 원의 둘레와 넓이를 구합니다.")
# print("원의 둘레:", circle.get_circumference())
# print("원의 넓이:", circle.get_area())

import math

# class Circle:
#     @property
#     def radius(self):
#         return self.__radius
#     @radius.setter
#     def radius(self, value):
#         if value <= 0:
#             raise TypeError("길이는양의 숫자여야 합니다.")
#             self.__radius = value
# print("# 데코레이터를 사용한 Getter와 Setter")
# circle = Circle(10)
# print("원래 원의 반지름: ", circle.radius)
# circle.radius = 2
# print("변경된 원의 반지름: ", circle.radius)
# print()
#
# print("#강제로 예외를 발생시킵니다.")
# circle.radius = -10

class CustomException(Exception):
    def __init__(self):
        super().__init__()
        print("#### 내가 만든 오류가 생성되었어요! ####")
    def __str__(self):
        return "오류가 발생했어요."
raise CustomException()