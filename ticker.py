# Crypto Ticker: the prices of the coins you pick, every 30 s. A wedgie has no internet of its own: its page on
# wedgie.dev (open in a tab) or `wedgie.py net` fetches for it (firmware net.py, 0.3.61+). Prices come from
# Alchemy through wedgie.dev (wedgie.json "net": "chain"; its key stays there): coins by symbol in one call,
# and tokens by address on their own chain (TOKENS), one call per chain.
# Green: pick coins. Grey (next to green): now. On the picker: green adds or removes a coin, red is done.
import time
import lcd as L
import ui
import net
import save

SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "LINK", "DOT", "LTC", "UNI", "AAVE", "ARB",
           "OP", "POL", "SUI", "NEAR", "TON", "HYPE", "SHIB", "PEPE")
TOKENS = {                          # name -> (chain, token address): any ERC-20 Alchemy prices
    "DEGEN": (8453, "0x4ed4e862860bed51a9570b96d89af5e1b0efefed"),
    "AERO": (8453, "0x940181a94a35a4569e4529a3cdfb74e38fd98631"),
    "BRETT": (8453, "0x532f27101965dd16442e59d40670faf5ebb142e4"),
}
COINS = SYMBOLS + tuple(TOKENS)
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
    out = {}
    syms = [c for c in mine if c in SYMBOLS]
    if syms:
        for c, v in net.chain(1, "wedgie_symbols", syms).items():
            out[c] = float(v)
    chains = {}
    for c in mine:
        if c in TOKENS:
            chains.setdefault(TOKENS[c][0], []).append(c)
    for ch, cs in chains.items():
        got = net.chain(ch, "wedgie_prices", [TOKENS[c][1] for c in cs])["tokens"]
        for c in cs:
            v = got.get(TOKENS[c][1])
            if v:
                out[c] = float(v)
    return out


def draw(d, mine, now, was, top):
    big = len(mine) <= 4                # a few coins: bigger rows
    row, rows = (46, 4) if big else (ROW, ROWS)
    d.fill(ui.WHITE)
    ui.band(d)
    if not now:
        ui.say(d, "No prices", 110, ui.MUTED, 2)
    for i, c in enumerate(mine[top:top + rows]):
        y = TOP + i * row
        p = now.get(c)
        s = dollars(p) if p else "?"
        ps = 3 if big and 24 * len(s) + 16 * len(c) + 8 <= 232 else 2
        if 8 * ps * len(s) + 16 * len(c) + 8 > 232:
            ps = 1 if 16 * len(s) + 8 * len(c) + 8 > 232 else 2
        ls = 2 if 8 * ps * len(s) + 16 * len(c) + 8 <= 232 else 1
        col = ui.INK if not p or c not in was or was[c] == p else (ui.GREEN_D if p > was[c] else ui.RED)
        d.big_text(c, 4, y + 4 * (ps - ls), ui.MUTED, ls)
        d.big_text(s, 236 - 8 * ps * len(s), y, col, ps)
        if i < rows - 1 and top + i + 1 < len(mine):
            d.hline(4, y + row - 7, 232, ui.GREY)
    if len(mine) > rows:
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
    ui.progress("Getting prices", "alchemy", bar=False)
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
                    ui.progress("Getting prices", "alchemy", bar=False)
                break
            if ("up" in k or "down" in k) and len(mine) > ROWS and now:
                top = max(0, min(len(mine) - ROWS, top + (1 if "down" in k else -1)))
                draw(d, mine, now, was, top)
            time.sleep_ms(50)
