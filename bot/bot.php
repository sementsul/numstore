<?php
/**
 * MagzGold — бот оформления номеров (PHP, cron-polling под Бегет).
 *
 * Флоу: /start → категории → список номеров → карточка → «Забронировать» →
 *        бронь (POST в API Безлимита с реф-привязкой) → ссылка на завершение у оператора.
 *
 * Запуск кроном раз в минуту:  php /home/USER/magzbot/bot.php
 * SSL не нужен (соединения исходящие), демон не нужен. Токен — в config.php (рядом, не в репозитории).
 * За один запуск скрипт long-poll'ит ~55 сек (быстрый ответ), затем выходит; следующий крон продолжает.
 */

$cfg = require __DIR__ . '/config.php';
$TOKEN     = $cfg['token'];
$API_TOKEN = $cfg['api_token'] ?? 'Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==';
$REF_ID    = $cfg['ref_id'] ?? '800848';
$KEY       = $cfg['key'] ?? '';

// Защита: если задан ключ — дёргать URL можно только с ?key=...
if ($KEY !== '' && (($_GET['key'] ?? '') !== $KEY)) { http_response_code(403); exit('forbidden'); }
@ignore_user_abort(true);
@set_time_limit(70);   // окно ~50с + обработка; ignore_user_abort — работаем даже после дисконнекта пингера

const API_BASE  = 'https://api.store.bezlimit.ru/v2';
const SITE      = 'https://magzgold.ru';
const UA        = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const PER_CAT   = 8;
$STORE_URL = 'https://l.bezlimit.ru/store/' . $REF_ID;

$CATS = [
    ['brilliant', '💎 Бриллиант'], ['platinum', 'Платина'], ['gold', 'Золото'],
    ['silver', 'Серебро'], ['bronze', 'Бронза'],
];
$CAT_LABEL = [];
foreach ($CATS as $c) { $CAT_LABEL[$c[0]] = $c[1]; }

$OFFSET_FILE = __DIR__ . '/offset.txt';
$LOCK_FILE   = __DIR__ . '/bot.lock';
$WATCH_FILE  = __DIR__ . '/watches.json';   // подписки: { "<chat_id>": { "<маска>": ["уже_уведомлённые_номера"] } }
$WCHECK_FILE = __DIR__ . '/watch_check.txt'; // время последней проверки подписок (троттлинг)

/* ---------- HTTP ---------- */
function http_get($url, $headers = [])
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 60,
        CURLOPT_USERAGENT => UA, CURLOPT_HTTPHEADER => $headers,
    ]);
    $r = curl_exec($ch); curl_close($ch);
    return $r ? json_decode($r, true) : null;
}
function http_post($url, $fields, $headers = [])
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 60, CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $fields, CURLOPT_USERAGENT => UA, CURLOPT_HTTPHEADER => $headers,
    ]);
    $r = curl_exec($ch); curl_close($ch);
    return $r ? json_decode($r, true) : null;
}

/* ---------- Telegram ---------- */
function tg($method, $params = [])
{
    global $TOKEN;
    foreach ($params as $k => $v) {
        if (is_array($v)) { $params[$k] = json_encode($v, JSON_UNESCAPED_UNICODE); }
    }
    return http_post("https://api.telegram.org/bot$TOKEN/$method", $params);
}
function kb($rows) { return ['inline_keyboard' => $rows]; }

/* Само-цепочка: в конце окна запускаем следующий заход (fire-and-forget) → бот работает непрерывно.
   Браузерный UA обязателен (анти-бот Бегета). flock в новом процессе не даст задвоения. */
function trigger_self()
{
    global $KEY;
    $host = $_SERVER['HTTP_HOST'] ?? 'd96179xw.beget.tech';
    $script = $_SERVER['SCRIPT_NAME'] ?? '/bot.php';
    $url = 'http://' . $host . $script . '?key=' . rawurlencode($KEY) . '&chain=1';
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_NOSIGNAL => 1,
        CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT_MS => 700,   // не ждём ответа
        CURLOPT_USERAGENT => 'Mozilla/5.0',
    ]);
    curl_exec($ch); curl_close($ch);
}

/* ---------- утилиты ---------- */
function digits_of($p) { return substr(preg_replace('/\D/', '', (string)$p), -10); }
function fmt_phone($p)
{
    $s = digits_of($p);
    return strlen($s) === 10
        ? '+7 ' . substr($s, 0, 3) . ' ' . substr($s, 3, 3) . '-' . substr($s, 6, 2) . '-' . substr($s, 8, 2)
        : '+7 ' . $s;
}
function fmt_money($n) { return ($n === null || $n === '') ? '' : number_format((int)$n, 0, '', ' ') . ' ₽'; }

/* ---------- данные Безлимита ---------- */
function fetch_by_cat($cat_key)
{
    global $API_TOKEN;
    $q = http_build_query(['expand' => 'tariff', 'is_reserved' => 'false',
                           'per_page' => '100', 'phone_pattern' => '9NNNNNNNNN']);
    $data = http_get(API_BASE . "/super-link/phones/mask-category?$q", ['Authorization: ' . $API_TOKEN]);
    $items = [];
    if (is_array($data)) {
        foreach ($data as $gk => $v) {
            if (trim(explode(',', $gk)[0]) === $cat_key && isset($v['items'])) { $items = $v['items']; break; }
        }
    }
    $out = [];
    foreach (array_slice($items, 0, PER_CAT) as $p) {
        $d = digits_of($p['phone'] ?? '');
        $t = $p['tariff'] ?? [];
        if (strlen($d) === 10 && !empty($t['id'])) {
            $out[] = ['d' => $d, 'phone' => $p['phone'], 'tid' => $t['id'], 'price' => $t['price'] ?? null];
        }
    }
    return $out;
}
function reserve($digits, $tariff_id)
{
    global $API_TOKEN, $REF_ID, $STORE_URL;
    $d = http_post(API_BASE . '/super-link/reservations?expand=super_link_uuid',
        ['phone' => $digits, 'tariff_id' => $tariff_id, 'type' => 'store',
         'user_id' => $REF_ID, 'filter' => 'professional'],
        ['Authorization: ' . $API_TOKEN]);
    $uuid = $d['super_link_uuid']['uuid'] ?? null;
    if (!$uuid) { return null; }
    return "$STORE_URL?type=p&cubes=$digits&uuid=" . rawurlencode($uuid);
}

/* ---------- экраны ---------- */
function screen_home($chat_id, $mid = null)
{
    global $CATS;
    $text = "<b>MagzGold</b> — красивые номера от партнёра «Безлимит».\n"
          . "Выберите категорию, чтобы посмотреть номера и забронировать 👇";
    $rows = [];
    foreach ($CATS as $c) { $rows[] = [['text' => $c[1], 'callback_data' => 'cat:' . $c[0]]]; }
    $rows[] = [['text' => '🌐 Открыть каталог', 'web_app' => ['url' => SITE . '/app/']]];
    $p = ['chat_id' => $chat_id, 'text' => $text, 'parse_mode' => 'HTML', 'reply_markup' => kb($rows)];
    if ($mid) { $p['message_id'] = $mid; tg('editMessageText', $p); }
    else { tg('sendMessage', $p); }
}
function screen_list($chat_id, $mid, $cat_key)
{
    global $CAT_LABEL;
    $nums = fetch_by_cat($cat_key);
    if (!$nums) {
        tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
            'text' => 'Сейчас нет доступных номеров в этой категории.',
            'reply_markup' => kb([[['text' => '← Назад', 'callback_data' => 'home']]])]);
        return;
    }
    $rows = [];
    foreach ($nums as $n) {
        $rows[] = [['text' => fmt_phone($n['phone']) . ' · ' . fmt_money($n['price']) . '/мес',
                    'callback_data' => "pick:{$n['d']}:{$n['tid']}"]];
    }
    $rows[] = [['text' => '← Категории', 'callback_data' => 'home']];
    tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
        'text' => '<b>' . ($CAT_LABEL[$cat_key] ?? 'Номера') . '</b> — выберите номер:',
        'parse_mode' => 'HTML', 'reply_markup' => kb($rows)]);
}
function screen_card($chat_id, $mid, $digits, $tid)
{
    $text = '<b>' . fmt_phone($digits) . "</b>\n\n"
          . "Как проходит оформление:\n"
          . "1️⃣ Загрузить фото паспорта РФ\n2️⃣ Подписать документы\n"
          . "3️⃣ Оплатить тариф\n4️⃣ Получить SIM (доставка по РФ бесплатно)\n\n"
          . "🔴 <b>Важно:</b> подключение только для граждан РФ.\nБронь удержит номер ~1 час.";
    $rows = [
        [['text' => '✅ Забронировать', 'callback_data' => "book:$digits:$tid"]],
        [['text' => '🔗 Открыть на сайте', 'url' => SITE . "/nomer/?p=$digits"]],
        [['text' => '← Назад', 'callback_data' => 'home']],
    ];
    tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
        'text' => $text, 'parse_mode' => 'HTML', 'reply_markup' => kb($rows)]);
}
function do_book($chat_id, $mid, $digits, $tid)
{
    tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
        'text' => 'Бронирую ' . fmt_phone($digits) . '…', 'parse_mode' => 'HTML']);
    $url = reserve($digits, $tid);
    if (!$url) {
        tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
            'text' => 'Не удалось забронировать ' . fmt_phone($digits) . ' — возможно, номер уже заняли. Попробуйте другой.',
            'reply_markup' => kb([[['text' => '← К категориям', 'callback_data' => 'home']]])]);
        return;
    }
    tg('editMessageText', ['chat_id' => $chat_id, 'message_id' => $mid,
        'text' => '✅ Номер <b>' . fmt_phone($digits) . "</b> забронирован на ~1 час.\n\n"
                . 'Завершите оформление у оператора (паспорт РФ + оплата):',
        'parse_mode' => 'HTML',
        'reply_markup' => kb([
            [['text' => '📝 Оформить номер', 'url' => $url]],
            [['text' => '← К категориям', 'callback_data' => 'home']],
        ])]);
}

/* ---------- роутинг ---------- */
/* ---------- ПОДПИСКИ на маски номеров ---------- */
function load_watches() { global $WATCH_FILE; return is_file($WATCH_FILE) ? (json_decode(file_get_contents($WATCH_FILE), true) ?: []) : []; }
function save_watches($w) { global $WATCH_FILE; file_put_contents($WATCH_FILE, json_encode($w, JSON_UNESCAPED_UNICODE)); }

// нормализуем маску к 10 символам: цифры — как есть, всё прочее → N (любая цифра)
function norm_mask($s)
{
    $s = strtoupper((string)$s);
    $s = preg_replace('/[^0-9N]/', 'N', $s);
    $s = substr(str_pad($s, 10, 'N'), 0, 10);
    return $s;
}
// человекочитаемо: +7 9•• •77 77 (N → •)
function mask_human($m)
{
    $m = str_replace('N', '•', norm_mask($m));
    return '+7 ' . substr($m, 0, 3) . ' ' . substr($m, 3, 3) . '-' . substr($m, 6, 2) . '-' . substr($m, 8, 2);
}
// живой поиск номеров по маске в API (все категории) → [digits => ['price'=>..]]
function search_pattern($pattern)
{
    global $API_TOKEN;
    $q = http_build_query(['expand' => 'tariff', 'is_reserved' => 'false', 'per_page' => '100', 'phone_pattern' => norm_mask($pattern)]);
    $data = http_get(API_BASE . "/super-link/phones/mask-category?$q", ['Authorization: ' . $API_TOKEN]);
    $out = [];
    if (is_array($data)) {
        foreach ($data as $v) {
            if (!isset($v['items'])) { continue; }
            foreach ($v['items'] as $p) {
                $d = digits_of($p['phone'] ?? '');
                if (strlen($d) === 10) { $out[$d] = ['price' => $p['tariff']['price'] ?? null]; }
            }
        }
    }
    return $out;
}
function add_watch($chat_id, $pattern)
{
    $m = norm_mask($pattern);
    if (strlen(str_replace('N', '', $m)) === 0) {
        tg('sendMessage', ['chat_id' => $chat_id, 'text' => 'Пустая маска — укажите хотя бы одну цифру. Пример: /watch NNNNNNN7777']);
        return;
    }
    $w = load_watches();
    $cid = (string)$chat_id;
    if (!isset($w[$cid])) { $w[$cid] = []; }
    if (!isset($w[$cid][$m])) { $w[$cid][$m] = []; }
    save_watches($w);
    tg('sendMessage', ['chat_id' => $chat_id, 'parse_mode' => 'HTML',
        'text' => "✅ Вы подписались на маску номеров\n<b>" . mask_human($m) . "</b>\n\nКак появятся соответствующие номера — мы вас обязательно уведомим.",
        'reply_markup' => kb([
            [['text' => '✖ Отписаться', 'callback_data' => 'unwatch:' . $m]],
            [['text' => '📋 Мои подписки', 'callback_data' => 'mywatches']],
        ])]);
}
function list_watches($chat_id, $mid = null)
{
    $w = load_watches();
    $cid = (string)$chat_id;
    $subs = $w[$cid] ?? [];
    if (!$subs) {
        $p = ['chat_id' => $chat_id, 'text' => "У вас нет подписок.\nЧтобы следить за номером — пришлите /watch и маску (напр. /watch NNNNNNN7777), или подпишитесь кнопкой на сайте."];
        if ($mid) { $p['message_id'] = $mid; tg('editMessageText', $p); } else { tg('sendMessage', $p); }
        return;
    }
    $rows = [];
    foreach (array_keys($subs) as $m) {
        $rows[] = [['text' => '🔔 ' . mask_human($m), 'callback_data' => 'noop']];
        $rows[] = [['text' => '✖ отписаться', 'callback_data' => 'unwatch:' . $m]];
    }
    $p = ['chat_id' => $chat_id, 'parse_mode' => 'HTML', 'text' => "<b>Ваши подписки на номера:</b>", 'reply_markup' => kb($rows)];
    if ($mid) { $p['message_id'] = $mid; tg('editMessageText', $p); } else { tg('sendMessage', $p); }
}
function remove_watch($chat_id, $pattern, $mid = null)
{
    $w = load_watches();
    $cid = (string)$chat_id;
    if (isset($w[$cid][$pattern])) { unset($w[$cid][$pattern]); if (!$w[$cid]) { unset($w[$cid]); } save_watches($w); }
    list_watches($chat_id, $mid);
}
// проверка всех подписок по API + уведомления. Троттлинг: не чаще раза в 30 мин.
function check_watches()
{
    global $WCHECK_FILE;
    $now = time();
    $last = is_file($WCHECK_FILE) ? (int)file_get_contents($WCHECK_FILE) : 0;
    if ($now - $last < 1800) { return; }
    file_put_contents($WCHECK_FILE, (string)$now);
    $w = load_watches();
    if (!$w) { return; }
    $patterns = [];
    foreach ($w as $subs) { foreach ($subs as $pat => $_) { $patterns[$pat] = 1; } }
    $found = [];
    foreach (array_keys($patterns) as $pat) { $found[$pat] = search_pattern($pat); }
    $changed = false;
    foreach ($w as $cid => $subs) {
        foreach ($subs as $pat => $notified) {
            foreach (($found[$pat] ?? []) as $d => $info) {
                if (in_array($d, $notified, true)) { continue; }
                tg('sendMessage', ['chat_id' => $cid, 'parse_mode' => 'HTML',
                    'text' => "🔔 Появился номер по вашей подписке!\n\n<b>" . fmt_phone($d) . "</b>"
                        . ($info['price'] ? ("\nТариф " . fmt_money($info['price']) . " /мес") : "")
                        . "\n\nОткрыть каталог: " . SITE . "/start/",
                    'reply_markup' => kb([[['text' => '🔎 Смотреть на сайте', 'url' => SITE . '/start/']], [['text' => '✖ отписаться', 'callback_data' => 'unwatch:' . $pat]]])]);
                $notified[] = $d; $changed = true;
            }
            if (count($notified) > 300) { $notified = array_slice($notified, -300); }
            $w[$cid][$pat] = $notified;
        }
    }
    if ($changed) { save_watches($w); }
}

function handle_update($u)
{
    if (isset($u['message']['text'])) {
        $chat_id = $u['message']['chat']['id'];
        $parts = preg_split('/\s+/', trim($u['message']['text']));
        $cmd = explode('@', $parts[0])[0];
        if ($cmd === '/start' && isset($parts[1]) && strpos($parts[1], 'watch_') === 0) { add_watch($chat_id, substr($parts[1], 6)); return; }
        if ($cmd === '/start' || $cmd === '/menu') { screen_home($chat_id); return; }
        if ($cmd === '/watch') {
            if (isset($parts[1])) { add_watch($chat_id, $parts[1]); }
            else { tg('sendMessage', ['chat_id' => $chat_id, 'text' => "Пришлите маску: /watch NNNNNNN7777 (N — любая цифра).\nИли подпишитесь кнопкой «🔔 Следить» на сайте."]); }
            return;
        }
        if ($cmd === '/mywatches' || $cmd === '/list') { list_watches($chat_id); return; }
        return;
    }
    if (!isset($u['callback_query'])) { return; }
    $cq = $u['callback_query'];
    $data = $cq['data'] ?? '';
    $chat_id = $cq['message']['chat']['id'];
    $mid = $cq['message']['message_id'];
    tg('answerCallbackQuery', ['callback_query_id' => $cq['id']]);
    if ($data === 'home') { screen_home($chat_id, $mid); }
    elseif ($data === 'mywatches') { list_watches($chat_id, $mid); }
    elseif ($data === 'noop') { /* заголовок-кнопка маски — ничего не делаем */ }
    elseif (strpos($data, 'unwatch:') === 0) { remove_watch($chat_id, substr($data, 8), $mid); }
    elseif (strpos($data, 'cat:') === 0) { screen_list($chat_id, $mid, substr($data, 4)); }
    elseif (strpos($data, 'pick:') === 0) { [, $d, $tid] = explode(':', $data); screen_card($chat_id, $mid, $d, $tid); }
    elseif (strpos($data, 'book:') === 0) { [, $d, $tid] = explode(':', $data); do_book($chat_id, $mid, $d, $tid); }
}

/* ---------- забор апдейтов за один HTTP-заход (~20 сек) ----------
   Дёргается внешним пингером (cron-job.org) раз в минуту. Короткий long-poll,
   пока есть сообщения; выходим по таймауту или когда очередь пуста. */
$lock = fopen($LOCK_FILE, 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) { exit('busy'); }   // другой заход активен

$offset = is_file($OFFSET_FILE) ? (int)file_get_contents($OFFSET_FILE) : 0;
// «Агрессивный» режим: держим соединение ~50с и НЕПРЕРЫВНО long-poll'им → покрываем почти всю минуту,
// ответ почти всегда мгновенный. ignore_user_abort позволяет работать даже после того, как пингер
// (cron-job.org) отвалится по своему таймауту ~30с — бот доработает окно до конца.
$deadline = time() + 50;
while (time() < $deadline) {
    $t = max(1, min(20, $deadline - time()));   // long-poll кусками ≤20с (чтобы перечитывать дедлайн)
    $q = ['timeout' => $t];
    if ($offset > 0) { $q['offset'] = $offset; }
    $resp = http_get('https://api.telegram.org/bot' . $TOKEN . '/getUpdates?' . http_build_query($q));
    foreach (($resp['result'] ?? []) as $u) {
        $offset = $u['update_id'] + 1;
        file_put_contents($OFFSET_FILE, (string)$offset);
        try { handle_update($u); } catch (\Throwable $e) { error_log('handle: ' . $e->getMessage()); }
    }
}
try { check_watches(); } catch (\Throwable $e) { error_log('watch: ' . $e->getMessage()); }  // проверка подписок (троттлинг 30 мин)
flock($lock, LOCK_UN); fclose($lock);
trigger_self();   // запускаем следующий заход → непрерывная работа (cron-job.org — лишь страховка)
echo 'ok';
