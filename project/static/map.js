require([
    "esri/Map", 
    "esri/views/MapView", 
    "esri/layers/GraphicsLayer", 
    "esri/Graphic"
], function(Map, MapView, GraphicsLayer, Graphic) {

    // Vytvoření mapy a mapového pohledu
    var map = new Map({
        basemap: "streets-navigation-vector"
    });

    var view = new MapView({
        container: "mapViewDiv",  // ID elementu v HTML
        map: map,
        center: [14.42076, 50.08804], // Souřadnice centra (Praha)
        zoom: 12
    });

    var layer = new GraphicsLayer();
    map.add(layer);

    // Načtení dat z backendu
    fetch("/api/data")
        .then(response => response.json())
        .then(data => {
            data.forEach(item => {
                var geometry = JSON.parse(item.geometry);
                var point = {
                    type: "point",
                    longitude: geometry.coordinates[0],
                    latitude: geometry.coordinates[1]
                };

                var symbol = {
                    type: "simple-marker",
                    color: "red",
                    size: "8px"
                };

                var graphic = new Graphic({
                    geometry: point,
                    symbol: symbol
                });

                layer.add(graphic);
            });
        })
        .catch(error => console.error("Chyba při načítání dat: ", error));
});
