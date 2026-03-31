#아이템 클래스 선언
class Item:
    def __init__(self, name, id, type, effect_value, description): #아이템 이름, 아이디, 종류, 효과, 설명
        self.name = name
        self.id = id
        self.type = type
        self.effect_value = effect_value
        self.description = description



