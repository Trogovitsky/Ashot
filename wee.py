import requests

# Конфигурация
OAUTH_TOKEN = "y0__xDg1sqxBRjB3RMg55n9pBL5budff01_hsyczOc2gbuUt2kmNg"  # Замените на реальный OAuth-токен Яндекс ID
IAM_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

def get_iam_token(oauth_token):
    """Запрашивает IAM-токен с использованием OAuth-токена"""
    headers = {"Content-Type": "application/json"}
    payload = {"yandexPassportOauthToken": oauth_token}
    
    try:
        response = requests.post(IAM_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json().get("iamToken")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе IAM-токена: {e}")
        return None

if __name__ == "__main__":
    iam_token = get_iam_token(OAUTH_TOKEN)
    if iam_token:
        print("IAM-токен успешно получен:")
        print(iam_token)
    else:
        print("Не удалось получить IAM-токен")