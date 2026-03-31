import item
import monster
import sys
import random
import skill
import copy
import os
import platform
import msvcrt
import item_data
import inven_test


# --- [함수 정의 구역] ---

def show_title_screen():
    """게임 시작 시 타이틀 화면을 표시합니다."""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    print("=" * 120)
    print("\n" * 2)
    print("      [포켓몬스터]".center(100))
    print("\n" * 1)
    print("            G A M E   S T A R T".center(100))
    print("\n" * 2)
    print("       계속하려면 엔터(Enter)를 누르세요...".center(100))
    print("\n" * 2)
    print("=" * 120)
    input()  # 사용자 입력을 대기

def show_game_over_screen():

    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    print("=" * 120)
    print("\n" * 2)
    print("      [포켓몬스터]".center(100))
    print("\n" * 1)
    print("            G A M E   O V E R".center(100))
    print("\n" * 2)
    print("       계속하려면 엔터(Enter)를 누르세요...".center(100))
    print("\n" * 2)
    print("=" * 120)
    input()  # 사용자 입력을 대기



def show_clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    print("=" * 120)
    print("\n" * 2)
    print("      [포켓몬스터]".center(100))
    print("\n" * 1)
    print("            G A M E   C L E A R".center(100))
    print("\n" * 2)
    print("       계속하려면 엔터(Enter)를 누르세요...".center(100))
    print("\n" * 2)
    print("=" * 120)
    input()  # 사용자 입력을 대기


def upgrade():
    global my_monster
    if my_monster.lv == 8:
        if my_monster.name == "불꽃숭이":
            my_monster = copy.deepcopy(monster.Monsters[4])
        elif my_monster.name == "모부기":
            my_monster = copy.deepcopy(monster.Monsters[6])
        elif my_monster.name == "팽도리":
            my_monster = copy.deepcopy(monster.Monsters[5])


def battle(my_monster, wild_monster):
    turn = 0
    # 화면을 지우고 전투 시작 알림
    clear_screen()
    print(f"\n[전투 발생!] 야생의 {wild_monster.name}(이)가 나타났다!")
    input("\n엔터를 누르면 전투를 시작합니다...")

    while my_monster.hp > 0 and wild_monster.hp > 0:
        if turn == 0:
            # 내 턴
            result = my_monster_turn(my_monster, wild_monster)
            if result == 2:  # 도망
                print("\n전투에서 무사히 도망쳤습니다!")
                input("엔터를 누르세요...")
                break
            turn = result

            if wild_monster.hp <= 0:
                clear_screen()
                print(f"\n★ 승리! {wild_monster.name}를 쓰러뜨렸습니다!")
                win_exp = 30 + wild_monster.lv * 5
                my_monster.gain_exp(win_exp)
                upgrade()
                input("\n엔터를 누르면 맵으로 돌아갑니다...")
                break
        else:
            # 상대 턴
            result = wild_monster_turn(my_monster, wild_monster)
            turn = result

            if my_monster.hp <= 0:
                clear_screen()
                print(f"\n세상에! {my_monster.name}(이)가 기절했습니다...")
                print("게임 오버.")
                show_game_over_screen()
                sys.exit()


def my_monster_turn(my_monster, wild_monster):
    while True:
        clear_screen()  # 매 턴 시작 시 화면을 지움
        print(f"=== [ {my_monster.name}  VS {wild_monster.name} ] ===")
        print(f"상대: {wild_monster.name} (HP: {wild_monster.hp})")
        print("-" * 40)
        print(f"나의 포켓몬: {my_monster.name}")
        print(f"Lv: {my_monster.lv} | 타입: {my_monster.m_type} | HP: {my_monster.hp}")
        print("-" * 40)
        print(f" 1: {my_monster.skill1} (위력: {my_monster.skill1.damage + (my_monster.lv - wild_monster.lv) * 0.5})")
        print(f" 2: {my_monster.skill2} (위력: {my_monster.skill2.damage + (my_monster.lv - wild_monster.lv) * 0.5})")
        print(" 3: 아이템 사용")
        print("-" * 40)

        try:
            choice = int(input("행동을 입력하세요 >> "))
            print()
        except ValueError:
            continue

        if choice == 1:
            print(f">>> {my_monster.name}의 {my_monster.skill1}!")
            my_monster.skill1.attack(my_monster, wild_monster)
            exp_gain = max(5, int(my_monster.skill1.damage * 0.5))  # 최소 5
            my_monster.gain_exp(exp_gain)
            upgrade()  #
            print("야생 포켓몬", wild_monster.name, "의 체력:", wild_monster.hp)
            print("+------------------------------------------\n")
            input("\n엔터를 눌러 다음으로...")  # 결과를 확인한 뒤 화면을 지우기 위해 대기
            return 1
        elif choice == 2:
            print(f">>> {my_monster.name}의 {my_monster.skill2}!")
            my_monster.skill2.attack(my_monster, wild_monster)
            exp_gain = max(5, int(my_monster.skill2.damage * 0.5))
            my_monster.gain_exp(exp_gain)
            upgrade()
            print("야생 포켓몬", wild_monster.name, "의 체력:", wild_monster.hp)
            print("+------------------------------------------\n")
            input("\n엔터를 눌러 다음으로...")
            return 1
        elif choice == 3:
            if not p_inven.items:
                print("사용할 아이템이 없습니다!")
                input("엔터를 누르세요...")
                continue
            return use_item_in_battle(my_monster)


def wild_monster_turn(my_monster, wild_monster):
    clear_screen()
    print(f"=== [ {my_monster.name} VS {wild_monster.name} ] ===")
    print(f"\n상대 {wild_monster.name}의 공격 차례입니다!")
    print("-" * 40)

    choice = random.choice([1, 2])
    if choice == 1:
        print(f">>> {wild_monster.name}의 {wild_monster.skill1}!")
        wild_monster.skill1.attack(wild_monster, my_monster)
    else:
        print(f">>> {wild_monster.name}의 {wild_monster.skill2}!")
        wild_monster.skill2.attack(wild_monster, my_monster)

    print(f"\n결과: {my_monster.name}의 남은 HP: {my_monster.hp}")
    print("-" * 40)
    input("\n엔터를 눌러 나의 턴으로...")
    return 0


# 화면을 지우는 헬퍼 함수
def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def use_item_in_battle(my_monster):
    print("\n인벤토리")
    for idx, (item_id, data) in enumerate(p_inven.items.items()):
        item_obj = data["item"]
        qty = data["quantity"]
        print(f"{idx + 1}. {item_obj.id} x{qty} - {item_obj.description}")
    print("0. 취소")

    while True:
        try:
            choice = int(input("사용할 아이템 번호 >> "))
            if choice == 0:
                return 0
            elif 1 <= choice <= len(p_inven.items):
                selected_item_id = list(p_inven.items.keys())[choice - 1]
                result = p_inven.use_item(selected_item_id, target=my_monster)
                input("엔터를 누르세요...")
                if result == 2:
                    return 2  # 도망
                else:
                    return 1  # 사용 후 턴 종료
            else:
                print("올바른 번호를 선택하세요.")
        except ValueError:
            print("숫자만 입력하세요.")


def draw_map():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

    maze = maze_list[current_map_index]
    print(f"=== 작은 숲 (MAP {current_map_index + 1}) ===")
    print("=" * 60)
    for y, row in enumerate(maze):
        line = ""
        for x, tile in enumerate(row):
            if x == p_x and y == p_y:
                line += T_PLAYER
            elif tile == 1:
                line += T_WALL
            elif tile == 2:
                line += T_GRASS
            elif tile == 3:
                line += T_PORTAL
            elif tile == 4:
                line += T_HEAL
            elif tile == 5:
                line += T_BOSS
            else:
                line += T_PATH
        print(line)
    print("=" * 60)
    print("\n['W,A,S,D'] 이동 | [Q] 종료 | [♥] 센터 | [:::] 풀숲")
    print("인벤토리 :", p_inven.get_inventory_summary())


# --- [게임 초기 설정 구역] ---

p_inven = inven_test.Inventory()

# 1. 타이틀 화면 먼저 실행
show_title_screen()

# 2. 오박사 등장 (화면 클리어 후)
if platform.system() == "Windows":
    os.system('cls')
else:
    os.system('clear')

print("\n오박사 : 오늘의 포켓몬은 뭘까요 ??"
      "\n허허, 드디어 모험을 떠나는구나! 원하는 포켓몬을 고르거라.\n")
print("1번: 불꽃숭이 (불꽃 타입)")
print("2번: 팽도리   (물 타입)")
print("3번: 모부기   (풀 타입)\n")

# 3. 몬스터 선택 루프
while True:
    try:
        choice = int(input("몬스터 번호를 입력하세요 >>> "))
        if choice == 1:
            my_monster = copy.deepcopy(monster.Monsters[0])
            print(f"\n[{my_monster.name}]를 선택하셨습니다!")
            break
        elif choice == 2:
            my_monster = copy.deepcopy(monster.Monsters[1])
            print(f"\n[{my_monster.name}]를 선택하셨습니다!")
            break
        elif choice == 3:
            my_monster = copy.deepcopy(monster.Monsters[2])
            print(f"\n[{my_monster.name}]를 선택하셨습니다!")
            break
        else:
            print("1, 2, 3 중에서만 선택해 주세요.")
    except ValueError:
        print("숫자만 입력해 주세요.")

input("\n모험을 시작하려면 엔터를 누르세요...")

# --- [맵 데이터 구역] ---

maze_list = [
    # Map 1
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 0, 2, 2, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 0, 2, 2, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 4, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 1, 1],
    ],
    # Map 2 (Boss)
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 4, 0, 0, 0, 0, 2, 2, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 1, 1, 1, 1],
    ]
]

# 타일 기호
T_WALL, T_GRASS, T_PATH, T_PLAYER = "###", ":::", "   ", " P "
T_PORTAL, T_HEAL, T_BOSS = " @ ", " ♥ ", " 🕱 "

current_map_index = 0
p_x, p_y = 9, 0

# --- [메인 게임 루프] ---

while True:
    draw_map()
    user_input = msvcrt.getch().decode('utf8').lower()

    if user_input == 'q':
        break

    next_x, next_y = p_x, p_y
    if user_input == 'w':
        next_y -= 1
    elif user_input == 's':
        next_y += 1
    elif user_input == 'a':
        next_x -= 1
    elif user_input == 'd':
        next_x += 1
    else:
        continue

    maze = maze_list[current_map_index]

    if 0 <= next_y < len(maze) and 0 <= next_x < len(maze[0]):
        target_tile = maze[next_y][next_x]

        if target_tile != 1:  # 벽이 아니면 이동
            p_x, p_y = next_x, next_y

            if target_tile == 2:  # 풀숲
                if random.random() < 0.4:  # 40% 확률로 전투
                    wild_monster = copy.deepcopy(monster.random_monster())
                    print(f"\n야생의 {wild_monster.name}이(가) 나타났다!")
                    input("전투를 시작하려면 엔터를 누르세요...")
                    battle(my_monster, wild_monster)

            elif target_tile == 0:  # 빈 길 (아이템 드롭)
                if random.random() < 0.15:  # 15% 확률
                    drop_item = random.choice(list(item_data.ITEM_DATABASE.values()))
                    p_inven.add_item(drop_item)
                    print(f"\n[획득] 바닥에서 {drop_item.id}을(를) 주웠습니다!")
                    input("엔터를 누르세요...")

            elif target_tile == 4:  # 포켓몬 센터
                print("\n[정보] 포켓몬 센터에 도착했습니다!")
                input("엔터를 누르면 체력이 회복됩니다...")
                my_monster.heal(100)
                print(f"{my_monster.name}의 체력이 모두 회복되었습니다.")
                input("엔터를 누르세요...")

            elif target_tile == 3:  # 포탈/보스
                print("\n[성공] 다음 지역으로 이동합니다!")
                input("엔터를 누르세요...")
                current_map_index += 1
                p_x, p_y = 9, 1

            elif target_tile == 5:

                wild_monster = copy.deepcopy(monster.Monsters[3])
                print("전설의 포켓몬 등장..!")
                print(wild_monster.name)
                print(wild_monster.m_type, )
                print(wild_monster.hp)
                print(wild_monster.skill1)
                print(wild_monster.skill2)
                print(wild_monster.skill3)
                print(wild_monster.skill4)
                print()
                battle(my_monster, wild_monster)
                print("게임을 종료합니다.")
                show_clear_screen()
                sys.exit()
