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
    // ... (podobně pro ostatní témata) ...

    echo "Území: " . $uzemi . "<br>";
    echo "Polygon: " . $user_polygon . "<br>";
    echo "Témata: " . implode(", ", $temata) . "<br>";
    echo "Podtémata: " . implode(", ", $podtemata) . "<br><br>";

    $command = "python spousteni_reportu_2.py " . escapeshellarg($uzemi) . " " . escapeshellarg($user_polygon) . " " . escapeshellarg(implode(",", $temata)) . " " . escapeshellarg(implode(",", $podtemata));
    exec($command, $output, $return_var);

    echo "Výstup Python skriptu:<br>";
    foreach ($output as $line) {
        echo $line . "<br>";
    }
}
?>