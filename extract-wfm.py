import json
import time
from playwright.sync_api import sync_playwright

# Standardized site slugs for reliable data fetching
ITEMS_SLUGS = {
    "Yareli Prime Full Set": "yareli_prime_set",
    "Yareli Prime Blueprint": "yareli_prime_blueprint",
    "Yareli Prime Chassis": "yareli_prime_chassis_blueprint",
    "Yareli Prime Neuroptics": "yareli_prime_neuroptics_blueprint",
    "Yareli Prime Systems": "yareli_prime_systems_blueprint"
}


def get_market_data():
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

        print("Connecting to the Warframe Market interface...")
        try:
            url = "https://warframe.market/items/yareli_prime_set"
            page.goto(url, wait_until="networkidle")
            time.sleep(2)
        except Exception as e:
            print(f"Initialization error : {e}")

        for name, slug in ITEMS_SLUGS.items():
            print(f"Extraction and filtering for : {name}...")

            # Retrieve the v2 ID using the slug, then load the orders
            js_script = f"""
            (async () => {{
                try {{
                    // 1. Find the v2 ID corresponding to the object's slug
                    const itemRes = await fetch("https://api.warframe.market/v2/items/{slug}");
                    const itemJson = await itemRes.json();
                    if (!itemJson || !itemJson.data || !itemJson.data.id) {{
                        return {{
                            "error": "Unable to find the ID for this component"
                        }};
                    }}
                    const itemId = itemJson.data.id;

                    // 2. Retrieve the orders with the correct ID
                    const res = await fetch("https://api.warframe.market/v2/orders/item/" + itemId + "?limit=15000");
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
    print("YARELI PRIME PRICE REPORT")
    print("="*50)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    get_market_data()
