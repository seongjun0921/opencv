class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, item, quantity = 1): # 아이템 추가했을 경우
        if item.id in self.items:
            self.items[item.id]["quantity"] += quantity
        else: self.items[item.id] = {"item": item, "quantity": quantity}
        print("{}를 획득! 현재 수량:{}".format(item.id, self.items[item.id]["quantity"]))

    def remove_item(self, item_id, quantity=1):
     if item_id in self.items:
        self.items[item_id]["quantity"] -= quantity
        if self.items[item_id]["quantity"] <= 0:
            del self.items[item_id]

    def show_inventory(self): #인벤토리 목록 보여주기
        print("인벤토리 목록")
        if not self.items:
            print("아이템이 없습니다.")
        for idx, data in enumerate(self.items.values()):
            item = data["item"]
            qty = data["quantity"]
            print(f"{idx+1}. {item.name} x{qty} - {item.description}")
        print("0. 나가기")

    def use_item(self, item_id, target=None, battle=None): #아이템 사용했을 경우
        if item_id not in self.items:
            print("아이템이 없다!")
            return 0

        item = self.items[item_id]["item"]

        if item.type == "heal": #heal 아이템 사용했을 경우 > hp 증가 결과
            target.hp = min(target.max_hp, target.hp + item.effect_value)
            print(f"{item.id} 사용! 체력 {item.effect_value} 회복 → 현재 HP: {target.hp}/{target.max_hp}")
            self.remove_item(item_id, 1)
            return 0
        elif item.type == "escape": #escape 아이템 사용했을 경우 > 도망침
            print("연막탄 사용! 도망쳤다!")
            self.remove_item(item_id, 1)
            return 2

    def get_inventory_summary(self):
        if not self.items:
            return "아이템 없음"

        summary = []
        for data in self.items.values():
            item = data["item"]
            qty = data["quantity"]
            summary.append(f"{item.id} x{qty}")
        return " | ".join(summary)