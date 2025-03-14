import sys
import json

print("Argumenty přijaté z PHP:")
for arg in sys.argv:
    print(arg)

uzemi = sys.argv[1]
user_polygon_json = sys.argv[2]
temata = sys.argv[3]
podtemata = sys.argv[4]

try:
    if user_polygon_json:
        user_polygon = json.loads(user_polygon_json)
    else:
        user_polygon = []  # Nastaví prázdné pole, pokud je JSON prázdné
    print("User Polygon (OBJECTIDs):", user_polygon)
except json.JSONDecodeError:
    print("Chyba při dekódování JSON pro userPolygon")

print("Území:", uzemi)
print("Témata:", temata)
print("Podtémata:", podtemata)

# ... (zpracování dat) ...