import json
import glob
import os
import requests


def send_discord_notification():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL variable is missing.")
        return

    # Read and sort JSON files
    all_results = []
    for filepath in glob.glob("result_*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                all_results.append(json.load(f))
            except json.JSONDecodeError:
                continue

    valid_results = [r for r in all_results if r.get("margin", 0) > 0]
    sorted_results = sorted(
        valid_results, key=lambda x: x["margin"], reverse=True
    )
    top_5 = sorted_results[:5]

    if not top_5:
        print("No profitable trades found.")
        return

    embeds = []
    colors = [0xFFD700, 0xC0C0C0, 0xCD7F32, 0x00FF00, 0x00FF00]

    for i, data in enumerate(top_5):
        wf_name = data["warframe"]
        details = data["details"]
        action_type = data.get("action_type", "unknown")

        # Helper: Link and Player Name
        def get_link_and_player(item_key):
            item = details.get(item_key, {})
            price = item.get('price', 'N/A')
            url = item.get('url', 'https://warframe.market')
            player = item.get('player', 'Unknown')
            return f"[{price} pl]({url}) (👤 {player})"

        # Helper: Formatted message (with or without spoiler)
        def get_whisper(item_key, spoiler=False):
            item = details.get(item_key, {})
            whisper = item.get('whisper', '')
            if whisper:
                # Discord syntax: || `text` ||
                msg = f"|| `{whisper}` ||" if spoiler else f"`{whisper}`"
                return msg
            unavail = "|| `Message unavailable` ||"
            return unavail if spoiler else "`Message unavailable`"

        # Constructing text blocks
        set_spoiler = action_type == "buy_parts"
        set_whisper = get_whisper(f"{wf_name} Prime Full Set",
                                  spoiler=set_spoiler)

        parts_spoiler = action_type == "buy_set"
        parts_whispers = (
            f"{get_whisper(f'{wf_name} Prime Blueprint', spoiler=parts_spoiler)}"
            f"\n{get_whisper(f'{wf_name} Prime Chassis', spoiler=parts_spoiler)}"
            f"\n{get_whisper(f'{wf_name} Prime Neuroptics', spoiler=parts_spoiler)}"
            f"\n{get_whisper(f'{wf_name} Prime Systems', spoiler=parts_spoiler)}"
        )

        # Base fields of the Embed
        fields = [
            {
                "name": "📦 Full Set",
                "value": get_link_and_player(f"{wf_name} Prime Full Set"),
                "inline": True
            },
            {
                "name": "🧩 Total Parts Cost",
                "value": f"**{data['parts_sum']} pl** total",
                "inline": True
            },
            {
                "name": "Parts Details",
                "value": (
                    f"**BP:** "
                    f"{get_link_and_player(f'{wf_name} Prime Blueprint')}\n"
                    f"**Chassis:** "
                    f"{get_link_and_player(f'{wf_name} Prime Chassis')}\n"
                    f"**Neuro:** "
                    f"{get_link_and_player(f'{wf_name} Prime Neuroptics')}\n"
                    f"**Systems:** "
                    f"{get_link_and_player(f'{wf_name} Prime Systems')}"
                ),
                "inline": False
            }
        ]

        # Sorting and displaying logic based on the most profitable action
        if action_type == "buy_parts":
            fields.append({
                "name": "✅ MAIN ACTION: Buy Parts (Copy to clipboard)",
                "value": parts_whispers,
                "inline": False
            })
            fields.append({
                "name": "🔄 Alternative: Buy Full Set (Spoiler)",
                "value": set_whisper,
                "inline": False
            })
        else:  # action_type == "buy_set"
            fields.append({
                "name": "✅ MAIN ACTION: Buy Full Set (Copy to clipboard)",
                "value": set_whisper,
                "inline": False
            })
            fields.append({
                "name": "🔄 Alternative: Buy Parts (Spoiler)",
                "value": parts_whispers,
                "inline": False
            })

        embed = {
            "title": f"#{i+1} - {wf_name} Prime",
            "color": colors[i] if i < len(colors) else 0x00FF00,
            "description": (
                f"**Recommendation:** {data['action']}\n"
                f"**Margin:** {data['margin']} pl"
            ),
            "fields": fields
        }
        embeds.append(embed)

    payload = {
        "content": "🚨 **Top 5 Warframe Market Trades!** 🚨",
        "embeds": embeds
    }

    response = requests.post(webhook_url, json=payload, timeout=10)
    if response.status_code == 204:
        print("Notification successfully sent to Discord!")
    else:
        print(f"Discord Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    send_discord_notification()
