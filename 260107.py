
class Monster:
    def __init__(self, name, type, hp):
        self.name = name
        self.type = type
        self.hp = hp


    # def get_damege(self):
    #     damage = 30
    #     return myMonster[2]  =  damage


Monsters = [
    Monster("불꽃숭", "불", 100),
    Monster("팽도리", "물", 100),
    Monster("꼬부기", "풀", 100)
]
print(type(Monsters[0].hp))

my_monster = int(input("""
1번 클릭: 불꽃숭
2번 클릭: 팽도리
3번 클릭: 꼬부기
몬스터를 고르세요 >>> 
"""))

if my_monster == 1:
    my_monster = Monsters[0]
    print("불꽃숭을 선택하셨습니다.")
elif my_monster == 2:
    my_monster = Monsters[1]
    print("팽도리을 선택하셨습니다.")
elif my_monster == 3:
    my_monster = Monsters[2]
    print("꼬부기을 선택하셨습니다.")
else:
    print("다시 입력하세요")



if __name__ == "__main__":
    print("이름\t\t", "타입\t", "hp")
    for Monster in Monsters:
        print(Monster.name, "\t", Monster.type, "\t", Monster.hp)

