import base64
import os
import pickle
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def generate_token(output_filename="token_ravi_kishan.pickle", secret_name="RAVI_KISHAN_TOKEN_BASE64"):
    print("=======================================================")
    print("      NEW YOUTUBE CHANNEL OAUTH TOKEN GENERATOR       ")
    print("=======================================================\n")
    print("Opening browser for OAuth authentication...")
    print("Please select/login to your NEW YouTube Channel account in the browser window.\n")

    candidate_secrets = [
        os.path.join("agentforchatvid", "client_secrets.json"),
        "client_secrets.json"
    ]
    
    client_secrets_file = None
    for p in candidate_secrets:
        if os.path.exists(p):
            client_secrets_file = p
            break

    if not client_secrets_file:
        raise FileNotFoundError("Could not find client_secrets.json! Please ensure client_secrets.json exists.")

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)

    creds = flow.run_local_server(port=0, prompt="select_account")

    json_file = output_filename.replace(".pickle", ".json") if output_filename.endswith(".pickle") else output_filename + ".json"
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    with open(output_filename, "wb") as f:
        pickle.dump(creds, f)

    print(f"\n[+] Credentials saved to: {json_file} and {output_filename}")

    # Read and encode JSON to Base64 for GitHub Actions Secret (cross-platform compatible)
    encoded_secret = base64.b64encode(creds.to_json().encode("utf-8")).decode("utf-8")

    print("\n=======================================================")
    print(f" GITHUB ACTION SECRET NAME: {secret_name}")
    print("=======================================================\n")
    print(encoded_secret)
    print("\n=======================================================")
    print("Copy the Base64 string above and add it as a secret in:")
    print("GitHub Repo -> Settings -> Secrets and variables -> Actions")
    print("=======================================================\n")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "token_ravi_kishan.pickle"
    sec_name = sys.argv[2] if len(sys.argv) > 2 else "RAVI_KISHAN_TOKEN_BASE64"
    generate_token(out_file, sec_name)
