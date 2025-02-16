from flask import Flask, render_template
import datetime

app = Flask(__name__)

# Seznam roků
roky = [2001, 2002, 2021, 2023, 2018, 2017, 2016, 2022, 2014, 2019, 2015]

# Funkce pro určení barvy na základě stáří roku
def zjisti_barvu(rok):
    aktualni_rok = datetime.datetime.now().year
    rozdil = aktualni_rok - rok
    if rozdil < 3:
        return "green"
    elif rozdil < 6:
        return "yellow"
    else:
        return "red"

# Hlavní cesta, která zobrazí HTML šablonu
@app.route("/")
def index():
    return render_template("index.html", roky=roky, zjisti_barvu=zjisti_barvu)

if __name__ == "__main__":
    app.run(debug=True)
