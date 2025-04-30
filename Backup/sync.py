# Local imports
from DatabaseManager import (
    preferences_manager,
    leads_manager,
    account_manager
)
# import json

# # Read leads from test.json
# with open('test.json', 'r') as file:
#     leads = json.load(file)

# followers = []

# for follower in followers:
#     account_manager.add_processed_account("4d283fe13044ba6182fc61f7258e3ee167209cd0d7eafc1dcf8d9d745392b465", {
#         "platform": "instagram", 
#         "source": account["metadata"]["username_id"], 
#         "follower_id": follower.get("id")
#         }
#     )

# leads = []

# for idx, lead in enumerate(leads):
#     print(lead)
#     leads_manager.add_lead("4d283fe13044ba6182fc61f7258e3ee167209cd0d7eafc1dcf8d9d745392b465", {
#             "lead_id": lead["lead_id"],
#             "platform": lead["lead_platform"], 
#             "phone_numbers": lead["lead_data"]["phone_numbers"],
#             "public_email": lead["lead_data"].get("email", ""),
#             "address": lead["lead_data"]["address"],
#             "websites": lead["lead_data"]["websites"],
#             "captured_at": lead["captured_at"],
#             "username": lead["lead_data"]["username"],
#             "full_name": lead["lead_data"]["name"],

#             "follower_count": lead["lead_data"]["followers"],
#             "following_count": lead["lead_data"]["following"],
#             "source": lead["source_account_id"]
#         }
#     )

# # Read leads from test.json
# with open('test.json', 'r') as file:
#     tracked_accounts = json.load(file)["tracked_accounts"]

# for idx, tracked_account in enumerate(tracked_accounts):
#     for processed_account_id in tracked_account["tracked_account_data"]["followers"]["usernames"].keys():
#         account_manager.add_processed_account(
#             "4d283fe13044ba6182fc61f7258e3ee167209cd0d7eafc1dcf8d9d745392b465",
#             {
#                 "platform": "instagram", 
#                 "source": tracked_account["tracked_account_username_id"], 
#                 "follower_id": processed_account_id
#             }
#         )

import json

# Read leads from test.json
with open('/Users/someguy/Desktop/Crushbase/Backup/test.json', 'r') as file:
    tracked_accounts = json.load(file)["tracked_accounts"]

for idx, tracked_account in enumerate(tracked_accounts):
    account_manager.add_tracked_account(
        "4d283fe13044ba6182fc61f7258e3ee167209cd0d7eafc1dcf8d9d745392b465",
        "instagram",
        tracked_account["tracked_account_username"],
        {
            "username_id": tracked_account["tracked_account_username_id"]
        }
    )