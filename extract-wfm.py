import json
import sys
import time
from playwright.sync_api import sync_playwright

# Read the requested Warframe from the command line and normalize it
# for later use.
if len(sys.argv) < 2:
    print("Error : Specify a Warframe (e.g., yareli)")
    sys.exit(1)

wf_name = sys.argv[1].lower().strip()
wf_capitalized = wf_name.capitalize()


# Normalize the Warframe name for consistent formatting
def normalize_warframe_name(wf_arg):
    wf_name = wf_arg.lower().strip()
    wf_capitalized = wf_name.capitalize()
    return wf_name, wf_capitalized


# Build a dictionary of item names and their
# corresponding slugs for the Warframe
def build_items_slugs(wf_name, wf_capitalized=None):
    if wf_capitalized is None:
        wf_name, wf_capitalized = normalize_warframe_name(wf_name)

    return {
        f"{wf_capitalized} Prime Full Set":
            f"{wf_name}_prime_set",
        f"{wf_capitalized} Prime Blueprint":
            f"{wf_name}_prime_blueprint",
        f"{wf_capitalized} Prime Chassis":
            f"{wf_name}_prime_chassis_blueprint",
        f"{wf_capitalized} Prime Neuroptics":
            f"{wf_name}_prime_neuroptics_blueprint",
        f"{wf_capitalized} Prime Systems":
            f"{wf_name}_prime_systems_blueprint",
    }


# Main function to extract market data for the specified Warframe
def get_market_data():
    items_slugs = build_items_slugs(wf_name, wf_capitalized)
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        print(
            f"Connecting to the Warframe Market interface for "
            f"{wf_capitalized}..."
        )
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
                results[name] = {"error": f"Error : {str(e)}"}

            time.sleep(1.5)  # Spam Protection

        browser.close()

    # Utility function to retrieve prices easily
    def get_price(item_name):
        return results.get(item_name, {}).get("price", 0)

    # Retrieval of all prices
    set_price = get_price(f"{wf_capitalized} Prime Full Set")
    bp_price = get_price(f"{wf_capitalized} Prime Blueprint")
    chassis_price = get_price(f"{wf_capitalized} Prime Chassis")
    neuro_price = get_price(f"{wf_capitalized} Prime Neuroptics")
    systems_price = get_price(f"{wf_capitalized} Prime Systems")

    # Total cost of individual components
    parts_sum = bp_price + chassis_price + neuro_price + systems_price
    margin = 0
    action = "Incomplete data"  # Default action if data is missing
    action_type = "unknown"  # Lets Discord know how to organize messages

    # Calculating the trade if all data is valid
    if (
        set_price > 0
        and parts_sum > 0
        and bp_price > 0
        and chassis_price > 0
        and neuro_price > 0
        and systems_price > 0
    ):
        if set_price > parts_sum:
            margin = set_price - parts_sum
            action = "BUY PARTS ➔ SELL SET"
            action_type = "buy_parts"
        else:
            margin = parts_sum - set_price
            action = "BUY SET ➔ SELL PARTS"
            action_type = "buy_set"

    # Add the URLs directly to the results so that notify.py can use them
    for name, slug in items_slugs.items():
        if name in results and "error" not in results[name]:
            results[name]["url"] = f"https://warframe.market/items/{slug}"

    # Building the final dictionary for export
    final_data = {
        "warframe": wf_capitalized,
        "margin": margin,
        "action": action,
        "action_type": action_type,
        "set_price": set_price,
        "parts_sum": parts_sum,
        "details": results  # Keeps all your original data
    }

    # Display in GitHub Actions logs
    print("\n" + "="*50)
    print(f"{wf_capitalized.upper()} PRIME : {action} (Marge: {margin} pl)")
    print("="*50)
    print("Overview of the data that will be sent to notify.py:")
    print(json.dumps(final_data, indent=2, ensure_ascii=False))
    print("="*50 + "\n")

    # Creation of the unique JSON file for this Warframe
    filename = f"result_{wf_name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    get_market_data()
