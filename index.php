<?php
/*
*
*  index.php - The main page of the control interface
*  By Kyle Gabriel
*  2012 - 2015
*
*/

####### Configure Edit Here #######

$install_path = "/var/www/mycodo";

########## End Configure ##########

$sensor_log = $install_path . "/log/sensor.log";
$mycodo_exe = $install_path . "/cgi-bin/mycodo";
$graph_exec = $install_path . "/cgi-bin/graph.sh";
$config_file = $install_path . "/config/mycodo.cfg";

if (version_compare(PHP_VERSION, '5.3.7', '<')) {
    exit("PHP Login does not run on PHP versions before 5.3.7, please update your version of PHP");
} else if (version_compare(PHP_VERSION, '5.5.0', '<')) {
    require_once("libraries/password_compatibility_library.php");
}
require_once('config/config.php');
require_once('translations/en.php');
require_once('libraries/PHPMailer.php');
require_once("classes/Login.php");
$login = new Login();

function readconfig($var) {
    global $config_file;
    $value = substr(`cat $config_file | grep $var | cut -d' ' -f3`, 0, -1);
    return $value;
}

if ($login->isUserLoggedIn() == true) {
    $page = isset($_GET['page']) ? $_GET['page'] : 'Main';

    $config_contents = file_get_contents($config_file);
    $config_rows = explode("\n", $config_contents);
    array_shift($config_rows);
    foreach($config_rows as $row => $data) {
        $row_data = explode(' = ', $data);
        if (!empty($row_data[1])) {
            ${$row_data[0]} = $row_data[1];
        }
    }
    
    $last_sensor = `tail -n 1 $sensor_log`;
    $sensor_explode = explode(" ", $last_sensor);
    $t_c = $sensor_explode[6];
    $t_f = round(($t_c * (9/5) + 32), 1);
    $hum = $sensor_explode[7];
    $dp_c = substr($sensor_explode[8], 0, -1);
    $dp_f = round(($dp_c * (9/5) + 32), 1);
    
    $time_now = `date +"%Y-%m-%d %H:%M:%S"`;
    $time_last = `tail -n 1 $sensor_log`;
    $time_explode = explode(" ", $time_last);
    $time_last = $time_explode[0] . '-' . $time_explode[1] . '-' . $time_explode[2] . ' ' . $time_explode[3] . ':' . $time_explode[4] . ':' . $time_explode[5];
?>
<html>
    <head>
        <title>Mycodo - <?php echo $page; ?></title>
        <link rel="stylesheet"  href="style.css" type="text/css" media="all" />
        <script type="text/javascript">
            function open_chmode() {
                window.open("changemode.php","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=500, height=630");
            }
            function open_legend() {
                window.open("image.php?span=legend","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=190, height=210");
            }
            function open_legend_full() {
                window.open("image.php?span=legend-full","_blank","toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=no, copyhistory=yes, width=600, height=385");
            }
        </script>
        <?php
            if (isset($_GET['r']) && ($_GET['r'] == 1)) echo "<META HTTP-EQUIV=\"refresh\" CONTENT=\"90\">";
        ?>
    </head>
    <body bgcolor="white">
        <table>
            <tr>
                <td width="160px" valign="top">
                    <table width="160px">
                    <tr>
                        <td align=center>
                            <div class="time">
                                <?php echo "Last page refresh<br> $time_now"; ?>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td align=center>
                            <div class="time">
                                <?php echo "Last sensor read<br> $time_last"; ?>
                            </div>
                        </td>
                    </tr>
                    <tr class="link">
                        <td>
                            <div class="sensor-block">
                                <div class="sensor-title">
                                    Temperature (PID <?php
                                        if ($tempor == 1) {
                                                echo "<span class=\"off\">OFF</span>";
                                            } else {
                                                echo "<span class=\"on\">ON</span>";
                                            }
                                    ?>)
                                </div>
                                <div class="sensor-values">
                                    <?php echo "Now: ${t_c}&deg;C (${t_f}&deg;F)"; ?>
                                </div>
                                <div class="setpoint">
                                    <?php echo "Set: ${settemp}&deg;C (${settemp_f}&deg;F)"; ?>
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr class="link">
                        <td>
                            <div class="sensor-block">
                                <div class="sensor-title">
                                    Humidity (PID <?php
                                        if ($humor == 1) {
                                                echo "<span class=\"off\">OFF</span>";
                                            } else {
                                                echo "<span class=\"on\">ON</span>";
                                            }
                                    ?>)
                                </div>
                                <div class="sensor-values">
                                    <?php echo "Now: ${hum}%"; ?>
                                </div>
                                <div class="setpoint">
                                    <?php echo "Set: ${sethum}%"; ?>
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr class="link">
                        <td>
                            <div class="sensor-block">
                                <div class="sensor-title">
                                    Dew Point
                                </div>
                                <div class="sensor-values">
                                    <?php echo "${dp_c}&deg;C (${dp_f}&deg;F)"; ?>
                                </div>
                            </div>
                        </td>
                    </tr>
                    <?php
                        menu_item('Main', 'Main', $page);
                        menu_item('1 Hour', 'Past Hour', $page);
                        menu_item('6 Hours', 'Past 6 Hours', $page);
                        menu_item('1 Day', 'Past Day', $page);
                        menu_item('1 Week', 'Past Week', $page);
                        menu_item('1 Month', 'Past Month', $page);
                        menu_item('1 Year', 'Past Year', $page);
                        menu_item('All', 'All', $page);
                    ?>
                    <tr>
                        <td class=link>
                            Legend: <a href="javascript:open_legend()">Brief</a> - <a href="javascript:open_legend_full()">Full</a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link>Refresh (90s): 
                            <?php
                                if (isset($_GET['r']) && $_GET['r'] == 1) {
                                    echo '<span class="on"><b>On</b></span> / <a href="index.php?page=$page">Off</a>';
                                } else echo '<a href="index.php?page=$page&r=1">On</a> / <span class="off"><b>Off</b></span>';
                            ?>
                        </td>
                    </tr>
                    <tr>
                        <td class=link>
                            Camera <a href="camera-still.php" target="_blank">Image</a> / <a href="camera-stream.php" target="_blank">Stream</a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link>
                            <a style="display: block;" href="history.php" target="_blank">View Logs</a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link>
                            <a style="display: block;" href="drawgraph.php" target="_blank">Custom Graph</a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link>
                            <a style="display: block;" href="javascript:open_chmode()">Configure Settings</a>
                        </td>
                    </tr>
                    <tr>
                        <td class=link-profile>
                            <div style="padding: 0px 0 5px 10px;">
                                Logged in as: <?php echo $_SESSION['user_name']; ?><?php if ($_SESSION['user_name'] != guest) { ?></div>
                            <div style="clear: both;"></div>
                            <img style="float: left; padding: 5px 5px 10px 10px; width: 50px; height: 50px;" src="<?php echo $login->user_gravatar_image_tag; ?>">
                            <div style="float: left; vertical-align: middle;">
                                <table>
                                <tr>
                                    <td class=link-profile>
                                        <a href="edit.php"><?php echo WORDING_EDIT_USER_DATA; ?></a>
                                    </td>
                                </tr>
                                <tr>
                                    <td class=link-profile>
                                        <a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a>
                                    </td>
                                </tr>
                                </table>
                                <?php } else { ?>
                                <br><a href="index.php?logout"><?php echo WORDING_LOGOUT; ?></a>
                            </div>
                            <?php } ?>
                        </td>
                    </tr>
                    </table>
                </td>
                <td width="830" valign="top">
                    <?php
                    if (isset($_GET['page'])) {
                        switch ($_GET['page']) {
                        case 'Main':
                        shell_exec($graph_exec . ' dayweek');
                        echo "<img src=image.php?span=main>";
                        break;
                        case '1 Hour':
                        shell_exec($graph_exec . ' 1h');
                        echo "<img src=image.php?span=1h>";
                        break;
                        case '6 Hours':
                        shell_exec($graph_exec . ' 6h');
                        echo "<img src=image.php?span=6h>";
                        break;
                        case '1 Day':
                        shell_exec($graph_exec . ' day');
                        echo "<img src=image.php?span=day>";
                        break;
                        case '1 Week':
                        shell_exec($graph_exec . ' week');
                        echo "<img src=image.php?span=week>";
                        break;
                        case '1 Month':
                        shell_exec($graph_exec . ' month');
                        echo "<img src=image.php?span=month>";
                        break;
                        case '1 Year':
                        shell_exec($graph_exec . ' year');
                        echo "<img src=image.php?span=year>";
                        break;
                        case 'All':
                        shell_exec($graph_exec . ' all');
                        echo "<img src=image.php?span=1h><p><img src=image.php?span=6h></p><p><img src=image.php?span=day></p><p><img src=image.php?span=week></p><p><img src=image.php?span=month></p><p><img src=image.php?span=year></p>";
                        break;
                        default:
                        shell_exec($graph_exec . ' dayweek');
                        echo "<img src=image.php?span=main>";
                        break;
                        }
                    } else {
                        shell_exec($graph_exec . ' dayweek');
                        echo "<img src=image.php?span=main>";
                    }
                    ?>
                </td>
            </tr>
        </table>
    </body>
</html>
<?php
} else include("views/not_logged_in.php");

function menu_item($id, $title, $current) {
    $class = ($current == $id) ? "active" : "inactive";

    echo '<tr><td class=' . $class . '>';
    if ($current != $id) {
        echo '<a style="display: block;" href="index.php?';
        if (isset($_GET['r'])){
            if ($_GET['r'] == 1) echo 'r=1&';
        }
        echo 'page=' . $id. '">' . $title . '</a>';
    } else echo $title;
    echo '</td></tr>';
}
?>
