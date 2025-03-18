from datetime import datetime
import uuid
import psycopg2
from rich import print
import matplotlib.pyplot as plt
import io
import base64
import geopandas as gpd
import json
from shapely.geometry import shape
import matplotlib.patches as mpatches
import contextily as ctx
import sys
from weasyprint import HTML
import webbrowser

# Nastavení výchozích hodnot pro argumenty
uzemi = ""
user_polygon_arg = ""
temata_arg = ""
podtemata_arg = ""

# Kontrola počtu argumentů a nastavení hodnot
if len(sys.argv) >= 2:
    uzemi = sys.argv[1]

if uzemi == 'uzivatelske':
    if len(sys.argv) >= 3:
        user_polygon_arg = sys.argv[2]
    if len(sys.argv) >= 4:
        temata_arg = sys.argv[3]
    if len(sys.argv) >= 5:
        podtemata_arg = sys.argv[4]
elif uzemi == 'cele':
    if len(sys.argv) >= 3:
        temata_arg = sys.argv[2]
    if len(sys.argv) >= 4:
        podtemata_arg = sys.argv[3]
else:
    print("Chyba: Neznámý typ území")
    sys.exit()  # Ukončíme skript, pokud je typ území neznámý

# Přidáno: Výpis argumentů
print('Argumenty:', sys.argv)

print(f"Hodnota uzemi v skriptu: {uzemi}")
print(f"Hodnota user_polygon v skriptu: {user_polygon_arg}")
print(f"Hodnota temata v skriptu: {temata_arg}")

if uzemi == 'uzivatelske':
    if user_polygon_arg:
        user_polygon_str = user_polygon_arg.strip()  # Odstranění mezer a prázdných znaků
        if user_polygon_str:
            user_polygon = [int(id) for id in user_polygon_str.split(',')]
            where_clause = "WHERE OBJECTID IN (" + ",".join(map(str, user_polygon)) + ")"
            print(f"user_polygon: {user_polygon}")
            print(f"where_clause: {where_clause}")
        else:
            user_polygon = []
            where_clause = ""
            print("Upozornění: user_polygon je prázdný!")
            print(f"user_polygon: {user_polygon}")
            print(f"where_clause: {where_clause}")
    else:
        user_polygon = []
        where_clause = ""
        print("Upozornění: user_polygon je prázdný!")
        print(f"user_polygon: {user_polygon}")
        print(f"where_clause: {where_clause}")
elif uzemi == 'cele':
    user_polygon = []
    user_polygon_arg = []
    where_clause = ""
    print("Zpracovávám celé území")
else:
    print("Chyba: Neznámý typ území")
def generate_report(uzemi, id_uzemi, temata_str, podtemata_str):
    print(f"Hodnota user_polygon v skriptu: {id_uzemi}")
    print(f"Hodnota uzemi v skriptu: {uzemi}")
    if not id_uzemi:
        print("Upozornění: user_polygon je prázdný!")

    # Rozsahy kategorií pro náchylnost k degradaci
    rozsahy_kategorii = {
        "N": (1.00, 1.17, "Neovlivněné území", "#1a9850"),
        "P": (1.17, 1.22, "Velmi nízká náchylnost k degradaci", "#66bd63"),
        "F1": (1.22, 1.26, "Nízká náchylnost k degradaci", "#a6d96a"),
        "F2": (1.26, 1.32, "Spíše nízká náchylnost k degradaci", "#d9ef8b"),
        "F3": (1.32, 1.37, "Střední náchylnost k degradaci", "#fee08b"),
        "C1": (1.37, 1.41, "Vysoká náchylnost k degradaci", "#fdae61"),
        "C2": (1.41, 1.53, "Velmi vysoká náchylnost k degradaci", "#f46d43"),
        "C3": (1.53, 2.00, "Extrémně vysoká náchylnost k degradaci", "#d73027"),
        "N/A": (None, None, "N/A", "#000000")  # Pro 0 vody
    }

    def urci_kategorii(vazeny_prumer):
        if vazeny_prumer is None:
            return "N/A", "N/A"

        for kod, (minimum, maximum, nazev, _) in rozsahy_kategorii.items():
            if minimum is not None and maximum is not None:
                if minimum <= vazeny_prumer <= maximum:
                    return f"{nazev} ({kod})", kod
            elif kod == "N/A" and vazeny_prumer is None:
                return "N/A", "N/A"

        return "Neznámá kategorie", None

    def urci_barvu_klasicke_meritko(meritko):
        meritko_cislo = int(meritko.replace("1:", "").replace(" ", ""))
        if meritko_cislo <= 10000:
            return "#006400", ""
        elif meritko_cislo <= 50000:
            return "#FFA500", "Měřítko má méně přesné rozlišení."
        else:
            return "#FF0000", "Měřítko velmi hrubé - Data je potřeba interpretovat obezřetně."

    def urci_barvu_meritko_na_pixel(meritko):
        meritko_cislo = int(meritko.replace("m/px", "").replace(" ", ""))
        if meritko_cislo <= 20:
            return "#006400", ""
        elif meritko_cislo <= 100:
            return "#FFA500", "Měřítko má méně přesné rozlišení."
        else:
            return "#FF0000", "Měřítko velmi hrubé - Data je potřeba interpretovat obezřetně."

    def urci_barvu_rok(rok):
        aktualni_rok = datetime.now().year
        rozdil = aktualni_rok - rok
        if rozdil < 3:
            return "#1a9641"
        elif rozdil < 5:
            return "#fdae61"
        else:
            return "#d7191c"

    dbname = 'DP_pokus'
    user = 'postgres'
    password = 'kapli4ky'
    host = 'localhost'
    port = '5432'

    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()
        print("Připojení k databázi bylo úspěšné")

        # Zpracování témat a podtémat
        temata = temata_str.split(',')
        podtemata = podtemata_str.split(',')

        if uzemi == 'uzivatelske' and user_polygon:
            ids_uzemi = user_polygon
            print(f"user_polygon: {user_polygon}")
            print(f"ids_uzemi: {ids_uzemi}")

            # Ověření, zda ID existují v databázi (s iterací)
            valid_ids = []
            for id_uzemi in ids_uzemi:
                try:
                    cursor.execute("SELECT id FROM cernovice_esai_na_ctverec WHERE id = %s", (id_uzemi,))
                    result = cursor.fetchone()
                    if result:
                        valid_ids.append(id_uzemi)
                        print(f"ID {id_uzemi} nalezeno v databázi.")  # Ladící výpis
                    else:
                        print(f"Upozornění: ID {id_uzemi} nebylo nalezeno v databázi.")
                except ValueError:
                    print(f"Upozornění: Neplatné ID {id_uzemi}.")

            if valid_ids:
                where_clause = f"WHERE id IN ({','.join(map(str, valid_ids))})"
                print(f"where_clause: {where_clause}")
            else:
                where_clause = ""
                print("Upozornění: Žádné platné ID nebyly nalezeny. Bude použit celý dataset.")
        else:
            ids_uzemi = []
            where_clause = ""
            print(f"user_polygon: {user_polygon}")
            print(f"where_clause: {where_clause}")

        sql_query_verohodnost_esai = "SELECT zkratka_txt, datovy_zdroj, indikator_cz, meritko, last_update, source_dat FROM metadata_dat"
        sql_query_funkce = f"SELECT AVG(hb_n) AS hodnota_hb, AVG(ctot_n) AS hodnota_uhlik, AVG(evap_n) AS hodnota_evapotranspirace FROM cernovice_esai_na_ctverec {where_clause};"
        sql_query_esai_hlavni = f"SELECT AVG(w_veget) AS \"Stav vegetace\", AVG(w_clim) AS \"Stav klimatu\", AVG(w_soil) AS \"Stav půdy\", AVG(w_mgm) AS \"Intenzita lidské činnosti\" FROM cernovice_esai_na_ctverec {where_clause};"
        sql_query_esai_podrobne = f"SELECT AVG(dra_w) AS \"Propustnost\", AVG(par_w) AS \"Matečná hornina\", AVG(dep_w) AS \"Hloubka půdy\", AVG(fra_w) AS \"Skeletovitost\", AVG(tex_w) AS \"Textura\", AVG(slo_w) AS \"Sklonitost svahu\", AVG(den_w) AS \"Hustota populace\", AVG(grw_w) AS \"Populační růst\", AVG(int_w) AS \"Intenzita využití půdy\", AVG(w_rai) AS \"Průměrný roční úhrn srážek\", AVG(arid_w) AS \"Index sucha\", AVG(asp_w) AS \"Orientace svahu\", AVG(dry_w) AS \"Odolnost vegetace vůči suchu\", AVG(ero_w) AS \"Schopnost vegetace bránit erozi\", AVG(pla_w) AS \"Pokryvnost vegetace\" FROM cernovice_esai_na_ctverec {where_clause};"
        sql_query_esai = f"SELECT AVG(w_esai) AS \"Zranitelnost krajiny\" FROM cernovice_esai_na_ctverec {where_clause};" 
                
        
        try:
            cursor.execute(sql_query_verohodnost_esai)
            data_verohodnost_esai = cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Chyba při provádění SQL dotazu pro věrohodnost ESAI: {e}")
            data_verohodnost_esai = []  # Nastavíme prázdný seznam, aby kód dále fungoval

        try:
            cursor.execute(sql_query_funkce)
            data_funkce = cursor.fetchall()[0] if cursor.rowcount > 0 else None
        except psycopg2.Error as e:
            print(f"Chyba při provádění SQL dotazu pro funkce: {e}")
            data_funkce = None  # Nastavíme None, aby kód dále fungoval

        try:
            cursor.execute(sql_query_esai)
            data_esai = cursor.fetchall()[0][0] if cursor.rowcount > 0 else None
        except psycopg2.Error as e:
            print(f"Chyba při provádění SQL dotazu pro ESAI: {e}")
            data_esai = None  # Nastavíme None, aby kód dále fungoval

        try:
            cursor.execute(sql_query_esai_hlavni)
            data_esai_hlavni = cursor.fetchall()[0] if cursor.rowcount > 0 else None
        except psycopg2.Error as e:
            print(f"Chyba při provádění SQL dotazu pro hlavní ESAI: {e}")
            data_esai_hlavni = None  # Nastavíme None, aby kód dále fungoval

        try:
            cursor.execute(sql_query_esai_podrobne)
            data_esai_podrobne = cursor.fetchall()[0] if cursor.rowcount > 0 else None
        except psycopg2.Error as e:
            print(f"Chyba při provádění SQL dotazu pro podrobné ESAI: {e}")
            data_esai_podrobne = None  # Nastavíme None, aby kód dále fungoval
 
        
        # Funkce pro získání barvy podle kategorie (PRO MAPY)
        def get_color_for_category_map(category):
            if category == 1:
                return '#d7191c'
            elif category == 2:
                return '#fdae61'
            elif category == 3:
                return '#ffffbf'
            elif category == 4:
                return '#a6d96a'
            elif category == 5:
                return '#1a9641'
            else:
                return 'gray'  # Pro neznámé kategorie
            
        def ziskej_data_pro_mapu(connection, sloupec_hodnot, where_clause, sloupec_geom='geom'):
            """Získá data z databáze pro generování mapy."""
            cursor = connection.cursor()
            sql_query_mapy = f"""
                SELECT ST_AsGeoJSON(ST_Transform({sloupec_geom}, 4326)) as geojson_str, {sloupec_hodnot}
                FROM cernovice_esai_na_ctverec {where_clause} WHERE ST_IsValid({sloupec_geom});
            """
            if where_clause:
                sql_query_mapy = sql_query_mapy.replace(f" {where_clause} WHERE", " WHERE")
            else:
                sql_query_mapy = sql_query_mapy.replace(f" {where_clause} WHERE", " WHERE")
            cursor.execute(sql_query_mapy)
            data_mapy = cursor.fetchall()
            return data_mapy

        def generuj_mapu(data, nazev_mapy, barvova_funkce):
            """Generuje mapu z dat."""
            geometries = []
            colors = []
            hodnoty = []
            for geojson_str, hodnota in data:
                try:
                    geojson_data = json.loads(geojson_str)
                    geom = shape(geojson_data)
                    geometries.append(geom)
                    color = barvova_funkce(hodnota)
                    colors.append(color)
                    hodnoty.append(hodnota)
                except Exception as e:
                    print(f"Chyba při zpracování GeoJSON: {e}")

            gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
            gdf = gdf.to_crs(epsg=3857)
            gdf['color'] = colors
            gdf['hodnota'] = hodnoty

            fig, ax = plt.subplots(figsize=(10, 10))
            gdf.plot(ax=ax, color=gdf['color'], edgecolor='grey', linewidth=0.2)
            ax.set_axis_off()
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.5)

            # Vytvoření legendy s popisky z obrázku
            kategorie_barvy = {
                1: ('Velmi nízká', '#d7191c'),
                2: ('Nízká', '#fdae61'),
                3: ('Střední', '#ffffbf'),
                4: ('Vysoká', '#a6d96a'),
                5: ('Velmi vysoká', '#1a9641')
            }
            patches = [mpatches.Patch(color=barva, label=nazev) for kategorie, (nazev, barva) in kategorie_barvy.items()]
            ax.legend(handles=patches, loc='lower right')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()
            buf.close()
            return img_base64

        # Definice indikátorů a jejich nastavení
        indikatory = [
            {"nazev": "Evapotranspirace", "sloupec_hodnot": "kat_evap_v", "barvova_funkce": get_color_for_category_map},
            {"nazev": "Zásoba uhlíku", "sloupec_hodnot": "kat_ctot_v", "barvova_funkce": get_color_for_category_map},
            {"nazev": "Ekologická hodnota biotopu", "sloupec_hodnot": "kat_hb_vyp", "barvova_funkce": get_color_for_category_map},
        ]

        mapy_base64 = {} #pro klasické mapy
        for indikator in indikatory:
            data = ziskej_data_pro_mapu(connection, indikator["sloupec_hodnot"], where_clause)
            mapy_base64[indikator["nazev"]] = generuj_mapu(data, indikator["nazev"], indikator["barvova_funkce"])





        # Funkce pro získání barvy podle kategorie (PRO MAPY ESAI)
        def get_color_for_esai_polygon(hodnota, rozsahy_kategorii):
            """Získá barvu pro polygon ESAI na základě hodnoty a sloupce."""
            if hodnota is None:
                return 'gray'  # Pro N/A
            # Využití rozsahy_kategorii pro získání barvy
            for kod, (minimum, maximum, _, barva) in rozsahy_kategorii.items():
                if minimum is not None and maximum is not None:
                    if minimum <= hodnota <= maximum:
                        return barva
            return 'gray'  # Pro neznámé hodnoty
        
        def generuj_mapu_esai(data, nazev_mapy, rozsahy_kategorii):
            """Generuje mapu ESAI s legendou."""
            geometries = []
            colors = []
            hodnoty = []
            for geojson_str, hodnota in data:
                try:
                    geojson_data = json.loads(geojson_str)
                    geom = shape(geojson_data)
                    geometries.append(geom)
                    color = get_color_for_esai_polygon(hodnota, rozsahy_kategorii)
                    colors.append(color)
                    hodnoty.append(hodnota)
                except Exception as e:
                    print(f"Chyba při zpracování GeoJSON: {e}")

            gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
            gdf = gdf.to_crs(epsg=3857)
            gdf['color'] = colors
            gdf['hodnota'] = hodnoty

            fig, ax = plt.subplots(figsize=(10, 10))
            gdf.plot(ax=ax, color=gdf['color'], edgecolor='grey', linewidth=0.2)
            ax.set_axis_off()
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.5)

            # Vytvoření legendy s popisky a barvami z rozsahy_kategorii
            patches = [mpatches.Patch(color=barva, label=nazev) for _, (_, _, nazev, barva) in rozsahy_kategorii.items()]
            ax.legend(handles=patches, loc='lower right')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()
            buf.close()
            return img_base64 

        # Definice indikátorů a jejich nastavení
        indikatory_esai = [
            {"nazev": "Zranitelnost krajiny (ESAI)", "sloupec_hodnot": "w_esai", "barvova_funkce": get_color_for_esai_polygon},
            {"nazev": "Stav vegetace", "sloupec_hodnot": "w_veget", "barvova_funkce": get_color_for_esai_polygon},
            {"nazev": "Stav klimatu", "sloupec_hodnot": "w_clim", "barvova_funkce": get_color_for_esai_polygon},
            {"nazev": "Stav půdy", "sloupec_hodnot": "w_soil", "barvova_funkce": get_color_for_esai_polygon},
            {"nazev": "Intenzita lidské činnosti", "sloupec_hodnot": "w_mgm", "barvova_funkce": get_color_for_esai_polygon},
        ]

        mapy_esai_base64 = {} #pro mapy esai
        for indikator in indikatory_esai:
            data = ziskej_data_pro_mapu(connection, indikator["sloupec_hodnot"], where_clause)
            mapy_esai_base64[indikator["nazev"]] = generuj_mapu_esai(data, indikator["nazev"], rozsahy_kategorii)

        if data_esai_hlavni is not None and len(data_esai_hlavni) == 4:
            hlavni_esai_kategorie = sorted(
                [("Stav vegetace", data_esai_hlavni[0]), ("Stav klimatu", data_esai_hlavni[1]), ("Stav půdy", data_esai_hlavni[2]), ("Intenzita lidské činnosti", data_esai_hlavni[3])],
                key=lambda x: x[1], reverse=True
            )
        else:
            print("Chyba: data_esai_hlavni jsou neplatná.")
            hlavni_esai_kategorie = [] # prázdný seznam pro vygenerování tabulky

        podrobne_esai = sorted(
        [("Propustnost", data_esai_podrobne[0]), ("Matečná hornina", data_esai_podrobne[1]), ("Hloubka půdy", data_esai_podrobne[2]), ("Skeletovitost", data_esai_podrobne[3]), ("Textura", data_esai_podrobne[4]), ("Sklonitost svahu", data_esai_podrobne[5]), ("Hustota populace", data_esai_podrobne[6]), ("Populační růst", data_esai_podrobne[7]), ("Intenzita využití půdy", data_esai_podrobne[8]), ("Průměrný roční úhrn srážek", data_esai_podrobne[9]), ("Index sucha", data_esai_podrobne[10]), ("Orientace svahu", data_esai_podrobne[11]), ("Odolnost vegetace vůči suchu", data_esai_podrobne[12]), ("Schopnost vegetace bránit erozi", data_esai_podrobne[13]), ("Pokryvnost vegetace", data_esai_podrobne[14])],
        key=lambda x: x[1], reverse=True
        )


        if data_funkce:
            hodnota_hb, hodnota_uhlik, hodnota_evapotranspirace = data_funkce
        else:
            hodnota_uhlik = "---"
            hodnota_evapotranspirace = "---"
            hodnota_hb = "---"

        def generuj_tabulku_hlavni_kategorie(hlavni_esai_kategorie, urci_kategorii, rozsahy_kategorii):
            tabulka_html = "<table><tr><th>Téma</th><th>Hodnota</th><th>Kategorie</th></tr>"
            for tema, hodnota in hlavni_esai_kategorie:
                kategorie, kod_kategorie = urci_kategorii(hodnota)
                barva_textu = rozsahy_kategorii[kod_kategorie][3] if kod_kategorie in rozsahy_kategorii else "#000000"
                tabulka_html += f"<tr><td><strong>{tema}</strong></td><td>{hodnota}</td><td style='color: {barva_textu};'>{kategorie}</td></tr>"
            tabulka_html += "</table>"
            return tabulka_html

        def generuj_tabulku_podrobna_temata(podrobne_esai, urci_kategorii, rozsahy_kategorii):
            tabulka_html = "<table><tr><th>Téma</th><th>Hodnota</th><th>Kategorie</th></tr>"
            for tema, hodnota in podrobne_esai:
                kategorie, kod_kategorie = urci_kategorii(hodnota)
                barva_textu = rozsahy_kategorii[kod_kategorie][3] if kod_kategorie in rozsahy_kategorii else "#000000"
                tabulka_html += f"<tr><td>{tema}</td><td>{hodnota}</td><td style='color: {barva_textu};'>{kategorie}</td></tr>"
            tabulka_html += "</table>"
            return tabulka_html

        tabulka_hlavni = generuj_tabulku_hlavni_kategorie(hlavni_esai_kategorie, urci_kategorii, rozsahy_kategorii)
        tabulka_podrobna = generuj_tabulku_podrobna_temata(podrobne_esai, urci_kategorii, rozsahy_kategorii)

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        id = uuid.uuid1()

        kategorie_esai, kod_kategorie_esai = urci_kategorii(data_esai)

        # Sbírání dat pro graf (pouze z podrobne_esai)
        kategorie_counts = {}
        for tema, hodnota in podrobne_esai:
            kategorie, _ = urci_kategorii(hodnota)
            kategorie_counts[kategorie] = kategorie_counts.get(kategorie, 0) + 1

        # Generování grafu
        kategorie_names = list(kategorie_counts.keys())
        counts = list(kategorie_counts.values())

        plt.figure(figsize=(10, 6))
        plt.bar(kategorie_names, counts)
        plt.xlabel("Kategorie zranitelnosti")
        plt.ylabel("Počet výskytů")
        plt.title("Zastoupení kategorií zranitelnosti (podrobné ESAI)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Uložení grafu do paměti
        buf = io.BytesIO()
        plt.savefig(buf, format="png")  # Uloží graf jako PNG do paměti
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode()  # Zakóduje graf do base64
        buf.close()



        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zranitelnost krajiny</title>
            <meta charset='UTF-8'>
            <meta name='description' content='HTML stránka georeportu zranitelnosti krajiny'>
            <meta name='keywords' content='zranitelnost krajiny, georeport, ekologie'>
            <meta name='author' content='Adéla Petřeková'>
            <style>
                @page {{
                    size: A4;
                    margin: 10mm 20mm;
                    @bottom-center {{
                        content: "Strana " counter(page);
                        font-family: Arial, sans-serif;
                        text-align: center;
                    }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                h1 {{
                    background-color: #4CAF50;
                    color: #fff;
                    padding: 10px;
                }}
                p {{
                    padding: 10px;
                }}
                .footer {{
                    position: fixed;
                    bottom: 0;
                    width: 100%;
                    text-align: center;
                }}
                .footer hr {{
                    width: 100%;
                    border: none;
                    border-top: 1px solid #000;
                    margin: 0;
                }}
                .footer-content {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 0;
                }}
                .footer img {{
                    height: 50px;
                }}
                .page_number {{
                    font-family: Arial, sans-serif;
                }}
                .indicator-box {{
                    border: 2px solid #4CAF50;
                    padding: 10px;
                    margin: 10px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .graf-container {{
                    max-width: 100%;
                    overflow-x: auto; /* Přidá horizontální posuvník, pokud je graf příliš široký */
                }}
                .graf-container img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>Název reportu: Zranitelnost krajiny</h1>
                <p>Lokalita: lokalita<br>
                Souřadnice: souradnice   <br>
                Datum a čas generování: {timestamp} <br>
                Unikatní identifikátor: {id}
                </p>
            </header>
            <main>
                <p> Tento report podává zprávu o degradaci krajiny na základě metody ESAI ....</p>
        """
        # Téma: Náchylnost krajiny
        if "nachylnost" in temata:
         html += f"""
                <h2> Krok I: Náchylnost krajiny k degradaci </h2>
                <p> Ve zvoleném území dosahuje výsledná hodnota náchylnosti k degradaci hodnoty <strong>{data_esai}</strong> a je klasifikována jako <span style="color: {rozsahy_kategorii[kod_kategorie_esai][3]};">{kategorie_esai}</span>.</p>
                {tabulka_hlavni}
        """
        if "nachylnost_hodnoty" in podtemata:
         html += f"""
                <h3> Podřazená témata </h3>
                {tabulka_podrobna}

        """

        serazene_podrobne_esai = sorted(podrobne_esai, key=lambda x: x[1], reverse=True)
        nejhorsi_indikatory = [f"<em>{tema}</em>" for tema, _ in serazene_podrobne_esai[:3]]
        html += "<div class='indicator-box'> Nejhorší 3 indikátory v zájmovém území jsou: " + ", ".join(nejhorsi_indikatory) + ".</div>"
        # Podtéma: Graf
        if "nachylnost_grafy" in podtemata:
         html += f"""
                <div class="graf-container">
                <h4>Graf: Zastoupení kategorií zranitelnosti (podrobné ESAI)</h4>
                <img src="data:image/png;base64,{image_base64}" alt="Graf zastoupení kategorií (podrobné ESAI)">
                </div>
        """
        # Podtéma: Mapa
        if "nachylnost_mapy" in podtemata:

            for nazev, img_base64 in mapy_esai_base64.items():
                html += f"""
                    <h2>{nazev}</h2>
                    <img src="data:image/png;base64,{img_base64}" width="800" height="600" alt="Mapa {nazev}">
                """

        html += f"""
                <h3> Věrohodnost dat </h3>
                <table>
                    <tr>
                        <th> Zkratka </th>
                        <th> Název </th>
                        <th> Datový zdroj </th>
                        <th> Garant </th>
                        <th> Měřítko </th>
                        <th> Rok aktualizace </th>
                    </tr>
        """

        for zkratka_txt, datovy_zdroj, indikator_cz, meritko, last_update, source_dat in data_verohodnost_esai:
            if "1:" in meritko:
                barva, poznamka = urci_barvu_klasicke_meritko(meritko)
            elif "m/px" in meritko:
                barva, poznamka = urci_barvu_meritko_na_pixel(meritko)
            barva_rok = urci_barvu_rok(last_update)

            html += f"""
                    <tr>
                        <td> {zkratka_txt} </td>
                        <td> {indikator_cz} </td>
                        <td> {datovy_zdroj} </td>
                        <td> {source_dat} </td>
                        <td style="color: {barva};"> {meritko} {poznamka} </td>
                        <td style="color: {barva_rok};"> {last_update} </td>
                    </tr>
            """

        html += f"""
                </table>"""
        # Téma: Funkčnost krajiny
        if "funkcnost" in temata:
            html += """
                <h2> Krok II: Posouzení funkčnosti krajiny </h2>
                <p> slouží k nalezení krajinných segmentů jejichž degradace bude mít velký/malý význam dopad na funkčnost krajiny </p>
            """
            # Podtéma: Hodnoty
            if "funkcnost_hodnoty" in podtemata:
                html += f"""
                    <table>
                        <tr>
                            <th> </th>
                            <th> Hodnota </th>
                            <th> Kategorie </th>
                        </tr>
                        <tr>
                            <td> Zásoba uhlíku ve vegetaci </td>
                            <td> {hodnota_uhlik} </td>
                            <td> Kategorie 1 </td>
                        </tr>
                        <tr>
                            <td> Evapotranspirace </td>
                            <td> {hodnota_evapotranspirace} </td>
                            <td> Kategorie 1 </td>
                        </tr>
                        <tr>
                            <td> Ekologická hodnota biotopu </td>
                            <td> {hodnota_hb} </td>
                            <td> Kategorie 1 </td>
                        </tr>
                        <tr>
                            <td> Vodoretence </td>
                            <td> Hodnota 1 </td>
                            <td> Kategorie 1 </td>
                        </tr>
                        <tr>
                            <td> Integrovaná hodnota </td>
                            <td> --- </td>
                            <td> Kategorie 1 </td>
                        </tr>
                    </table>
                """
            # Podtéma: Graf
            if "funkcnost_grafy" in podtemata:
                html += "<p>zde patrří graf funkčnosti</p>"

            # Podtéma: Mapa
            if "funkcnost_mapy" in podtemata:
                # Vložení map do HTML
                for nazev, img_base64 in mapy_base64.items():
                    html += f"""
                        <h2>{nazev}</h2>
                        <img src="data:image/png;base64,{img_base64}" width="800" height="600" alt="Mapa {nazev}">
                    """

            html += f"""
                <h3> Věrohodnost dat </h3>
                <table>
                    <tr>
                        <th> Název </th>
                        <th> Datový zdroj geometrie/KB </th>
                        <th> Garant </th>
                        <th> Měřítko </th>
                        <th> Rok aktualizace </th>
                    </tr>
                    <tr>
                        <td> Indikátor 1 </td>
                        <td> Hodnota 1 </td>
                        <td> Věrohodnost 1 </td>
                        <td> meritko </td>
                        <td> ROK </td>
                    </tr>
                </table>
            """
        # Téma: Odolnost krajiny
        if "odolnost" in temata:
            html += "<h2> Krok III: Odolnost krajiny </h2>"

            # Podtéma: Hodnoty
            if "odolnost_hodnoty" in podtemata:
                html += "<p>zde hodnoty odolnosti</p>"

            # Podtéma: Graf
            if "odolnost_grafy" in podtemata:
                html += "<p>zde graf odolnosti</p>"

            # Podtéma: Mapa
            if "odolnost_mapy" in podtemata:
                html += "<p>zde mapa odolnosti</p>"

        # Téma: Syntéza
        if "synteza" in temata:
            html += "<h2> Krok IV: Syntéza/lokalizace prioritních opatření </h2>"

            # Podtéma: Hodnoty
            if "synteza_hodnoty" in podtemata:
                html += "<p>zde hodnoty syntezy</p>"

            # Podtéma: Graf
            if "synteza_grafy" in podtemata:
                html += "<p>zde graf syntezy</p>"

            # Podtéma: Mapa
            if "synteza_mapy" in podtemata:
                html += "<p>zde mapa syntezy</p>"

        # Téma: Typizace
        if "typizace" in temata:
            html += "<h2> Krok V: Typizace prioritních opatření </h2>"

            # Podtéma: Hodnoty
            if "typizace_hodnoty" in podtemata:
                html += "<p>zde hodnoty typizace</p>"

            # Podtéma: Graf
            if "typizace_grafy" in podtemata:
                html += "<p>zde graf typizace</p>"

            # Podtéma: Mapa
            if "typizace_mapy" in podtemata:
                html += "<p>zde mapy typizace</p>"

        html += """
            </main>
            <footer>
                <div class="footer">
                    <hr>
                    <div class="footer-content">
                        <img src="katedra_logo.png" alt="Logo KGI">
                        <img src="logo_czechglobe.png" alt="Logo CzechGlobe">
                    </div>
                </div>
            </footer>
        </body>
        </html>
        """

        

        print("HTML report byl úspěšně vygenerován.")
    except Exception as error:
        print(f"Chyba při zpracování databáze nebo generování mapy: {error}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


    # Vytvoření HTML souboru
    if 'html' in locals(): # kontrola jestli html existuje.
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"""{html}""")

        print("HTML report byl úspěšně vygenerován.")

        # output html as a PDF
        HTML("index.html").write_pdf("index.pdf")

        print("Generated index.pdf")
        #otevření pdf souboru
        webbrowser.open("index.pdf")
    else:
        print("Generování html souboru bylo přerušeno chybou")

if __name__ == "__main__":
    generate_report(uzemi, user_polygon, temata_arg, podtemata_arg)
else:
    print("Chyba: Neplatný počet argumentů. Použití: python spousteni_georeportu.py <uzemi> <user_polygon> <temata> <podtemata>")


