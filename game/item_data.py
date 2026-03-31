from item import Item
 #아이템 데이터
potion = Item("potion", "상처약", "heal", 20, "포켓몬의 체력을 20 회복한다.")
super_potion = Item("super", "고급 상처약", "heal", 50, "체력을 50 회복한다.")
escape_rope = Item("escape", "연막탄", "escape", 1, "전투에서 도망친다.")

ITEM_DATABASE = {
    "potion" : potion,
    "super_potion" : super_potion,
    "escape_rope" : escape_rope
}





