class Skill:
    def __init__(self, name, damage, skill_type):
        self.name = name
        self.damage = damage
        self.skill_type = skill_type

    def __str__(self):
        return self.name

    def attack(self, attacker, enemy):
        # 기본 데미지
        hp = self.damage

        # 레벨 차 보정
        level_bonus = (attacker.lv - enemy.lv) * 0.5

        # 상성 보정
        if self.skill_type == "풀":
            if enemy.m_type == "물":
                hp += 10
                print_strong()
            elif enemy.m_type == "불":
                hp -= 10
                print_weak()

        elif self.skill_type == "불":
            if enemy.m_type == "풀":
                hp += 10
                print_strong()
            elif enemy.m_type == "물":
                hp -= 10
                print_weak()

        elif self.skill_type == "물":
            if enemy.m_type == "불":
                hp += 10
                print_strong()
            elif enemy.m_type == "풀":
                hp -= 10
                print_weak()

        # 레벨 보정 적용
        hp += level_bonus

        # 최소 데미지 보장
        hp = max(1, int(hp))

        enemy.hp -= hp
        print_damage(hp)

# 포켓몬별 각각 스킬 함수
class head(Skill):
    def __init__(self):
        super().__init__("몸통박치기",20,"노멀")

class tree(Skill):
    def __init__(self):
        super().__init__("잎날가르기",30,"풀")


class fire(Skill):
    def __init__(self):
        super().__init__("화염방사",30,"불")


class water(Skill):
    def __init__(self):
        super().__init__("물대포", 30,"물")

class punch(Skill):
    def __init__(self):
        super().__init__("용의숨결",40,"노멀")

class fire2(Skill):
    def __init__(self):
        super().__init__("불대문자",35,"불")

class water2(Skill):
    def __init__(self):
        super().__init__("파도타기",35,"물")

class tree2(Skill):
    def __init__(self):
        super().__init__("풀베기",35,"풀")

def print_damage(hp):
    print("입힌 데미지: ", hp)

def print_strong():
    print("증가된 데미지를 입혔다.")

def print_weak():
    print("감소된 데미지를 입혔다.")