# Crypto Ticker: the prices of the coins you pick, every 30 s. A wedgie has no internet of its own: its page on
# wedgie.dev (open in a tab) or `wedgie.py net` fetches for it (firmware net.py, 0.3.61+), only from
# api.coinbase.com (wedgie.json "net"). One request gets every coin: Coinbase's USD exchange rates, picked.
# Green: pick coins. Grey (next to green): now. On the picker: green adds or removes a coin, red is done.
import time
import lcd as L
import ui
import net
import save

COINS = ("BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "LINK", "DOT", "LTC", "UNI", "AAVE", "ARB",
         "OP", "POL", "SUI", "NEAR", "TON", "SHIB", "PEPE")
URL = "https://api.coinbase.com/v2/exchange-rates?currency=USD"
EVERY = 30000
ROWS = 6
ROW = 30
TOP = 36


def commas(i):
    out = ""
    while len(i) > 3:
        out, i = "," + i[-3:] + out, i[:-3]
    return i + out


def dollars(p):
    if p >= 1000:
        return "$" + commas(str(int(p + 0.5)))
    if p >= 1:
        return "$%.2f" % p
    s = "%.8f" % p                      # 4 digits after the zeros: $0.07716, $0.00000489
    i = 2
    while i < len(s) and s[i] == "0":
        i += 1
    return "$" + s[:min(len(s), i + 4)].rstrip("0").rstrip(".")


def fetch(mine):
    r = net.get(URL, pick={c: "data.rates." + c for c in mine})
    out = {}
    for c in mine:
        try:
            out[c] = 1 / float(r.get(c))
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    return out


def draw(d, mine, now, was, top):
    d.fill(ui.WHITE)
    ui.band(d)
    if not now:
        ui.say(d, "No prices", 110, ui.MUTED, 2)
    for i, c in enumerate(mine[top:top + ROWS]):
        y = TOP + i * ROW
        p = now.get(c)
        s = dollars(p) if p else "?"
        sc = 2 if 16 * (len(c) + len(s) + 1) <= 232 else 1
        col = ui.INK if not p or c not in was or was[c] == p else (ui.GREEN_D if p > was[c] else ui.RED)
        d.big_text(c, 4, y + (0 if sc == 2 else 4), ui.MUTED, sc)
        d.big_text(s, 236 - 8 * sc * len(s), y + (0 if sc == 2 else 4), col, sc)
        if i < ROWS - 1 and top + i + 1 < len(mine):
            d.hline(4, y + ROW - 7, 232, ui.GREY)
    if len(mine) > ROWS:
        ui.say(d, "^ v more", 212, ui.MUTED)
    ui.say(d, "{g} coins  {k} now", 226, ui.MUTED)
    d.show()


def pick(d, keys, mine):
    """The coin list: green adds or removes one, red is done. Returns the coins in COINS order."""
    on = set(mine)
    at = top = 0
    while True:
        d.fill(ui.WHITE)
        ui.band(d)
        for i, c in enumerate(COINS[top:top + ROWS]):
            y = TOP + i * ROW
            if top + i == at:
                d.fill_rect(0, y - 4, 240, ROW - 2, ui.INK)
            d.big_text(c, 12, y, ui.WHITE if top + i == at else ui.INK, 2)
            if c in on:
                d.big_text("+", 212, y, ui.GREEN, 2)
        ui.say(d, "{g} add/remove  {r} done", 226, ui.MUTED)
        d.show()
        k = ()
        while not k:
            k = keys.pressed()
            time.sleep_ms(30)
        if "up" in k:
            at = (at - 1) % len(COINS)
        elif "down" in k:
            at = (at + 1) % len(COINS)
        elif "A" in k or "press" in k:
            c = COINS[at]
            if c in on:
                if len(on) > 1:
                    on.discard(c)
            else:
                on.add(c)
        elif "Y" in k:
            return [c for c in COINS if c in on]
        top = min(max(top, at - ROWS + 1), at)


def run():
    d = L.LCD()
    keys = L.Keys()
    mine = save.load("coins", ["BTC", "ETH", "SOL"])
    mine = [c for c in mine if c in COINS] or ["BTC", "ETH", "SOL"]
    ui.progress("Getting prices", "coinbase.com", bar=False)
    now, was, top = {}, {}, 0
    while True:
        try:
            got = fetch(mine)
            was, now = now, got
            draw(d, mine, now, was, top)
        except net.Error as e:
            ui.page(d, "No internet", [(str(e), ui.MUTED)], hint="{k} try again")
        t = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t) < EVERY:
            k = keys.pressed()
            if "X" in k:
                break
            if "A" in k or "press" in k:
                new = pick(d, keys, mine)
                if new != mine:
                    mine, top = new, 0
                    try:
                        save.store("coins", mine)
                    except OSError:
                        pass
                    now, was = {}, {}
                    ui.progress("Getting prices", "coinbase.com", bar=False)
                break
            if ("up" in k or "down" in k) and len(mine) > ROWS and now:
                top = max(0, min(len(mine) - ROWS, top + (1 if "down" in k else -1)))
                draw(d, mine, now, was, top)
            time.sleep_ms(50)
