import json
import sys
import time
from playwright.sync_api import sync_playwright

# Read the requested Warframe from the command line and normalize it for later use.
if len(sys.argv) < 2:
    print("Error : Specify a Warframe (e.g., yareli)")
    sys.exit(1)

wf_name = sys.argv[1].lower().strip()
wf_capitalized = wf_name.capitalize()


def normalize_warframe_name(wf_arg):
    wf_name = wf_arg.lower().strip()
    wf_capitalized = wf_name.capitalize()
    return wf_name, wf_capitalized


def build_items_slugs(wf_name, wf_capitalized=None):
    if wf_capitalized is None:
        wf_name, wf_capitalized = normalize_warframe_name(wf_name)

    return {
        f"{wf_capitalized} Prime Full Set": f"{wf_name}_prime_set",
        f"{wf_capitalized} Prime Blueprint": f"{wf_name}_prime_blueprint",
        f"{wf_capitalized} Prime Chassis": f"{wf_name}_prime_chassis_blueprint",
        f"{wf_capitalized} Prime Neuroptics": f"{wf_name}_prime_neuroptics_blueprint",
        f"{wf_capitalized} Prime Systems": f"{wf_name}_prime_systems_blueprint",
    }


def get_market_data():
    items_slugs = build_items_slugs(wf_name, wf_capitalized)
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                "Safari/537.36"
            )
        )
        page = context.new_page()

        print(f"Connecting to the Warframe Market interface for {wf_capitalized}...")
        try:
            url = f"https://warframe.market/items/{wf_name}_prime_set"
            page.goto(url, wait_until="networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"Initialization error : {e}")

        for name, slug in items_slugs.items():
            print(f"Extraction and filtering for : {name}...")

            # Retrieve the v2 ID using the slug, then load the orders
            js_script = f"""
            (async () => {{
                try {{
                    // 1. Find the v2 ID corresponding to the object's slug
                    const itemRes = await fetch(
                        "https://api.warframe.market/v2/items/{slug}"
                    );
                    const itemJson = await itemRes.json();
                    if (!itemJson || !itemJson.data || !itemJson.data.id) {{
                        return {{
                            "error": "Unable to find the ID for this component"
                        }};
                    }}
                    const itemId = itemJson.data.id;

                    // 2. Retrieve the orders with the correct ID
                    const ordersUrl =
                        "https://api.warframe.market/v2/orders/item/" +
                        itemId +
                        "?limit=15000";
                    const res = await fetch(ordersUrl);
                    const json = await res.json();

                    if (!json || !json.data) {{
                        return {{
                            "error": "No orders found"
                        }};
                    }}

                    const validOrders = json.data.filter(o =>
                        o.type === "sell" &&
                        o.user &&
                        o.user.platform === "pc" &&
                        o.user.status === "ingame"
                    );

                    if (validOrders.length === 0) {{
                        return {{
                            "error": "There are currently no in-game vendors"
                        }};
                    }}

                    validOrders.sort((a, b) => a.platinum - b.platinum);
                    const cheapest = validOrders[0];

                    return {{
                        "price": cheapest.platinum,
                        "player": cheapest.user.ingameName
                    }};
                }} catch (e) {{
                    return {{ "error": e.message }};
                }}
            }})()
            """

            try:
                data = page.evaluate(js_script)

                if "error" in data:
                    results[name] = {"error": data["error"]}
                else:
                    whisper_text = (
                        f"/w {data['player']} Hi! I want to buy: {name} "
                        f"for {data['price']} platinum. (warframe.market)"
                    )
                    results[name] = {
                        "price": data["price"],
                        "player": data["player"],
                        "whisper": whisper_text
                    }

            except Exception as e:
                results[name] = {"error": f"Erreur : {str(e)}"}

            time.sleep(1.5)  # Spam Protection

        browser.close()

    print("\n" + "="*50)
    print(f"{wf_capitalized.upper()} PRIME PRICE REPORT")
    print("="*50)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    get_market_data()
