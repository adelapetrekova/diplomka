<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $uzemi = $_POST["uzemi"];
    $user_polygon = isset($_POST["userPolygon"]) ? $_POST["userPolygon"] : "[]"; // Nastaví prázdné pole, pokud není nastaveno

    $temata = isset($_POST["tema"]) ? $_POST["tema"] : [];
    $podtemata = [];

    if (in_array("nachylnost", $temata)) {
        if (isset($_POST["nachylnost_hodnoty"])) $podtemata[] = "nachylnost_hodnoty";
        if (isset($_POST["nachylnost_grafy"])) $podtemata[] = "nachylnost_grafy";
        if (isset($_POST["nachylnost_mapy"])) $podtemata[] = "nachylnost_mapy";
    }
    if (in_array("funkcnost", $temata)) {
        if (isset($_POST["funkcnost_hodnoty"])) $podtemata[] = "funkcnost_hodnoty";
        if (isset($_POST["funkcnost_grafy"])) $podtemata[] = "funkcnost_grafy";
        if (isset($_POST["funkcnost_mapy"])) $podtemata[] = "funkcnost_mapy";
    }
    if (in_array("odolnost", $temata)) {
        if (isset($_POST["odolnost_hodnoty"])) $podtemata[] = "odolnost_hodnoty";
        if (isset($_POST["odolnost_grafy"])) $podtemata[] = "odolnost_grafy";
        if (isset($_POST["odolnost_mapy"])) $podtemata[] = "odolnost_mapy";
    }
    if (in_array("synteza", $temata)) {
        if (isset($_POST["synteza_hodnoty"])) $podtemata[] = "synteza_hodnoty";
        if (isset($_POST["synteza_grafy"])) $podtemata[] = "synteza_grafy";
        if (isset($_POST["synteza_mapy"])) $podtemata[] = "synteza_mapy";
    }
    if (in_array("typizace", $temata)) {
        if (isset($_POST["typizace_hodnoty"])) $podtemata[] = "typizace_hodnoty";
        if (isset($_POST["typizace_grafy"])) $podtemata[] = "typizace_grafy";
        if (isset($_POST["typizace_mapy"])) $podtemata[] = "typizace_mapy";
    }

    echo "Území: " . $uzemi . "<br>";
    echo "Polygon: " . $user_polygon . "<br>";
    echo "Témata: " . implode(", ", $temata) . "<br>";
    echo "Podtémata: " . implode(", ", $podtemata) . "<br><br>";

    $command = "python spousteni_georeportu.py " . escapeshellarg($uzemi) . " " . escapeshellarg($user_polygon) . " " . escapeshellarg(implode(",", $temata)) . " " . escapeshellarg(implode(",", $podtemata));
    exec($command, $output, $return_var);

    echo "Výstup Python skriptu:<br>";
    foreach ($output as $line) {
        echo $line . "<br>";
    }
}
?>