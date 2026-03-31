import random
import skill
import sys

class Monster:
    def __init__(self, name, m_type, hp, skill1, skill2, skill3,skill4, lv, exp = 0, exp_to_next=100):
        self.name = name
        self.m_type = m_type
        self.hp = hp
        self.skill1 = skill1
        self.skill2 = skill2
        self.skill3 = skill3
        self.skill4 = skill4
        self.max_hp = hp
        self.lv = lv
        self.exp = exp
        self.exp_to_next = exp_to_next

    #hp 관리
    # def get_damage(self, damage, m_type, s_type): #damage = skill모듈에서 정해진 데미지 값 이후 수정필요
    # if self.hp - damage > 0:
    # self.hp -= damage
    #
    # else:
    # self.hp = 0
    # print("hp: {}".format(self.hp))
            # print("님 사망")
            # sys.exit()\

    #hp 100(max_hp)이상이면 100 아니면 + heal
    # heal = 상처약 변수 --> heal item 모듈 보고 수정 필요

    # def heal(self, heal):
    #     if self.hp + heal >=100:
    #         self.hp = 100
    #         print(self.name, "hp: {}".format(self.hp))
    #     else:
    #         self.hp += heal
    #         print(self.name, "hp: {}".format(self.hp))

    def gain_exp(self,amount):
        if amount <= 0:
            return

        self.exp += amount
        print(f"[경험치] {self.name} 경험치 +{amount} (현재 {self.exp}/{self.exp_to_next})")

        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level_up()

    def level_up(self):
        self.lv += 1
        print(f"[레벨업] {self.name} 레벨이 {self.lv}이(가) 되었습니다! (남은 EXP {self.exp}/{self.exp_to_next})")
#랜덤 몬스터 생성 함수
def random_monster():
    return random.choice(Monsters[0:3])

#몬스터 종류
Monsters = [
    Monster("불꽃숭이", "불", 100, skill.fire(), skill.head(),skill.fire(), skill.head(),5),
    Monster("팽도리", "물", 100, skill.water(), skill.head(),skill.water(), skill.head(),5),
    Monster("모부기", "풀", 100, skill.tree(), skill.head(),skill.tree(), skill.head(),5),
    Monster("펄기아","노멀",150,skill.tree(), skill.fire(),skill.water(), skill.punch(),30),
    Monster("초염몽", "불", 150, skill.fire2(), skill.head(), skill.water(), skill.head(),8),
    Monster("엠페르트", "물", 150, skill.water2(), skill.head(), skill.tree(), skill.head(),8),
    Monster("토대부기", "풀", 150, skill.tree2(), skill.head(), skill.water(), skill.punch(),8),
]


# if __name__ == "__main__":
# print("이름\t\t", "타입\t", "hp \t", "skill1 \t", "skill2")
# for Monster in Monsters:
# print(Monster.name, "\t", Monster.m_type, "\t", Monster.hp, "\t", Monster.skill1, "\t", Monster.skill2)
#
# print()
# print(Monsters[0].skill1.skill_type)