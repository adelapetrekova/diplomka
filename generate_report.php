<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $uzemi = isset($_POST["uzemi"]) ? $_POST["uzemi"] : null;
    $userPolygon = isset($_POST["userPolygon"]) ? $_POST["userPolygon"] : null;
    $tema = isset($_POST["tema"]) ? $_POST["tema"] : [];

    $podtema = [];
    foreach ($tema as $t) {
        if (isset($_POST[$t . "_hodnoty"])) {
            $podtema[] = $t . "_hodnoty";
        }
        if (isset($_POST[$t . "_grafy"])) {
            $podtema[] = $t . "_grafy";
        }
        if (isset($_POST[$t . "_mapy"])) {
            $podtema[] = $t . "_mapy";
        }
    }

    $podtema_string = implode(",", $podtema);

    $uzemi_arg = escapeshellarg($uzemi);
    $userPolygon_arg = escapeshellarg($userPolygon);
    $podtema_arg = escapeshellarg($podtema_string);

    $python_script = "C:\\ms4w\\Apache\\htdocs\\DP\\spousteni_georeportu.py";
    $command = "python " . escapeshellarg($python_script) . " " . $uzemi_arg . " " . $userPolygon_arg . " " . $podtema_arg;

    $output = shell_exec($command);
    echo "<pre>$output</pre>";
} else {
    echo "Formulář nebyl odeslán.";
}
?>